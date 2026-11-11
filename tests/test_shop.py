import unittest
from datetime import datetime

from flask import Flask, g

from app import Client, Pay, Product, ProductPurchase, Trener, db, init_shop, login_manager
from routes import register_routes
from app import upgrade_payment_timestamps
from sqlalchemy import create_engine, inspect, text


class ShopTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder='../templates', static_folder='../static')
        self.app.config.update(TESTING=True, SECRET_KEY='test', SQLALCHEMY_DATABASE_URI='sqlite://')
        db.init_app(self.app)
        login_manager.init_app(self.app)
        register_routes(self.app, db, Client, Trener, Product, Pay, ProductPurchase)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        init_shop()
        db.session.add_all([
            Client(id='buyer', name='Покупатель', email='buyer@example.com', password='test', gender='Мужской'),
            Client(id='other', name='Другой', email='other@example.com', password='test', gender='Мужской'),
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def sign_in(self, user='buyer'):
        g.pop('_login_user', None)
        with self.client.session_transaction() as session:
            session['_user_id'] = user
            session['_fresh'] = True

    def test_catalog_and_database_details(self):
        init_shop()
        self.assertEqual(Product.query.count(), 5)
        response = self.client.get('/shop')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text.count('<article class="shop-card">'), 5)
        for product in Product.query.all():
            self.assertIn(product.name, self.client.get('/shop/' + product.id).text)
        product = db.session.get(Product, 'bottle')
        product.description = 'Обновлённое описание из базы'
        db.session.commit()
        self.assertIn(product.description, self.client.get('/shop/bottle').text)
        self.assertEqual(self.client.get('/shop/missing').status_code, 404)

    def test_checkout_and_ownership(self):
        self.assertEqual(self.client.get('/payment/product-bottle').status_code, 302)
        self.sign_in()
        self.assertEqual(self.client.get('/payment/product-bottle').status_code, 200)
        with self.client.session_transaction() as session:
            token = session['shop_checkout_token']
        data = {'checkout_token': token, 'price': '1', 'email': 'other@example.com'}
        response = self.client.post('/payment/product-bottle', data=data)
        self.assertEqual(response.status_code, 302)
        purchase = ProductPurchase.query.one()
        self.assertEqual(purchase.product_id, 'bottle')
        self.assertEqual(purchase.payment.summa, 1200)
        self.assertEqual(purchase.payment.email, 'buyer@example.com')
        self.assertTrue(purchase.payment.payment)
        self.assertIsNotNone(purchase.payment.created_at)
        self.assertEqual(purchase.payment.status, 'Оплачено')
        self.assertIn('/payment_success.html?', response.location)
        success = self.client.get(response.location)
        self.assertEqual(success.status_code, 200)
        self.assertIn('Товар успешно оплачен.', success.text)
        self.assertIn(purchase.payment.tarif, success.text)
        self.assertEqual(self.client.get(response.location).status_code, 200)
        self.assertEqual(Pay.query.count(), 1)
        self.assertEqual(self.client.post('/payment/product-bottle', data=data).status_code, 400)
        self.assertEqual(Pay.query.count(), 1)
        self.sign_in('other')
        self.assertEqual(self.client.get(response.location).status_code, 404)

    def test_existing_plans_and_invalid_checkout(self):
        self.sign_in()
        for plan_id in ('month', 'six_months', 'year'):
            self.assertEqual(self.client.get('/payment/' + plan_id).status_code, 200)
        self.assertIn('Абонемент успешно оформлен.', self.client.post('/payment_success.html').text)
        self.assertEqual(self.client.get('/payment/product-missing').status_code, 404)
        self.assertEqual(self.client.post('/payment/product-bottle').status_code, 400)
        self.assertEqual(Pay.query.count(), 0)

    def test_membership_payment_is_saved_and_not_duplicated(self):
        self.sign_in()
        page = self.client.get('/payment/six_months')
        self.assertIn('action="/payment/six_months"', page.text)
        with self.client.session_transaction() as session:
            token = session['shop_checkout_token']
        data = {'checkout_token': token, 'price': '1'}
        response = self.client.post('/payment/six_months', data=data)
        self.assertEqual(response.status_code, 302)
        payment = Pay.query.one()
        self.assertEqual(payment.tarif, 'Будь в форме')
        self.assertEqual(payment.summa, 50000)
        self.assertEqual(payment.status, 'Оплачено')
        self.assertTrue(payment.payment)
        self.assertIsNotNone(payment.created_at)
        self.assertEqual(ProductPurchase.query.count(), 0)
        success = self.client.get(response.location)
        self.assertEqual(success.status_code, 200)
        self.assertIn('Будь в форме', success.text)
        self.assertIn('Абонемент успешно оформлен.', success.text)
        self.assertEqual(self.client.post('/payment/six_months', data=data).status_code, 400)
        self.assertEqual(Pay.query.count(), 1)
        self.sign_in('other')
        self.assertEqual(self.client.get(response.location).status_code, 404)

    def test_history_is_private_and_shows_all_payment_statuses(self):
        self.assertEqual(self.client.get('/personal_ac').status_code, 302)
        self.sign_in()
        self.assertIn('У вас пока нет покупок.', self.client.get('/personal_ac').text)
        for item_id in ('product-bottle', 'year'):
            self.client.get('/payment/' + item_id)
            with self.client.session_transaction() as session:
                token = session['shop_checkout_token']
            self.client.post('/payment/' + item_id, data={'checkout_token': token})
        db.session.add_all([
            Pay(id='unpaid', email='buyer@example.com', summa=2000, tarif='Неоплаченный товар',
                payment=False, status='Не оплачено'),
            Pay(id='private', email='other@example.com', summa=3333, tarif='Чужая покупка',
                payment=True, status='Оплачено'),
        ])
        db.session.commit()
        history = self.client.get('/personal_ac')
        self.assertEqual(history.status_code, 200)
        for text in ('Бутылка SOPRANO', 'Максимум возможностей', '1 200 ₽', '100 000 ₽',
                     'Оплачено', 'Неоплаченный товар', 'Не оплачено'):
            self.assertIn(text, history.text)
        self.assertNotIn('Чужая покупка', history.text)
        self.sign_in('other')
        history = self.client.get('/personal_ac')
        self.assertIn('Чужая покупка', history.text)
        self.assertNotIn('Бутылка SOPRANO', history.text)

    def test_history_sorts_by_purchase_time_and_shows_moscow_time(self):
        self.sign_in()
        # Insert out of chronological order; IDs also must not determine the order.
        db.session.add_all([
            Pay(id='z', email='buyer@example.com', summa=100, tarif='Старая покупка',
                created_at=datetime(2026, 11, 10, 22, 30), status='Оплачено'),
            Pay(id='a', email='buyer@example.com', summa=200, tarif='Новая покупка',
                created_at=datetime(2026, 11, 11, 12, 5, 9), status='Оплачено'),
            Pay(id='m', email='buyer@example.com', summa=300, tarif='Архивная покупка',
                created_at=datetime(2026, 1, 1), status='Не оплачено'),
        ])
        db.session.commit()
        # Simulate a legacy record whose date was never recorded.
        db.session.execute(text("UPDATE payment SET created_at = NULL WHERE id = 'm'"))
        db.session.commit()
        history = self.client.get('/personal_ac').text
        self.assertLess(history.index('Новая покупка'), history.index('Старая покупка'))
        self.assertLess(history.index('Старая покупка'), history.index('Архивная покупка'))
        self.assertIn('11.11.2026 15:05:09', history)
        self.assertIn('11.11.2026 01:30:00', history)
        self.assertIn('2026-11-11T15:05:09+03:00', history)
        self.assertIn('Дата неизвестна', history)

    def test_old_database_upgrade_preserves_records_and_is_repeatable(self):
        engine = create_engine('sqlite://')
        try:
            with engine.begin() as connection:
                connection.execute(text('CREATE TABLE payment (id TEXT PRIMARY KEY, summa INTEGER)'))
                connection.execute(text("INSERT INTO payment VALUES ('old', 1200)"))
            upgrade_payment_timestamps(engine)
            upgrade_payment_timestamps(engine)
            self.assertIn('created_at', {c['name'] for c in inspect(engine).get_columns('payment')})
            with engine.connect() as connection:
                row = connection.execute(text('SELECT id, summa, created_at FROM payment')).one()
                self.assertEqual(tuple(row), ('old', 1200, None))
        finally:
            engine.dispose()


if __name__ == '__main__':
    unittest.main()
