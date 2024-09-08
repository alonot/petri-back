from django.test import TestCase

class BasicAccount(TestCase):
    def create(self) -> None:
        self.client.post('/api/register/', data={
            'username': 'hey',
            'email': 'hey@hey.in',
            'password': 'hey',
            'phone': '1213131',
            'college': 'hey',
            'year': '3',
        })
