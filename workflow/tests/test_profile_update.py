from django import test
from django.urls import reverse

from bs4 import BeautifulSoup

from factories import UserFactory, TolaUserFactory, CountryFactory


class TestProfileUpdates(test.TestCase):
    def setUp(self):
        super(TestProfileUpdates, self).setUp()

        self.afghanistan = CountryFactory(country='Afghanistan', code='AF')
        self.myanmar = CountryFactory(country='Myanmar', code='MM')
        self.usa = CountryFactory(country='United States', code='US')

        self.user = UserFactory(first_name="FN", last_name="LN", username="tester")
        self.user.set_password('password')
        self.user.save()
        self.tola_user = TolaUserFactory(user=self.user, country=self.usa)
        self.tola_user.countries.add(self.afghanistan, self.usa)
        self.tola_user.save()

        self.countries_assigned = {self.afghanistan.id, self.usa.id}

    def test_superuser_can_save(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()

        client = test.Client()
        client.login(username="tester", password='password')

        response = client.post(reverse('profile'), data={
            'title': '',
            'name': self.tola_user.name,
            'employee_number': self.tola_user.employee_number,
            'user': self.user.id,
            'country': self.usa.id,
            'language': 'fr',
            'countries': [self.afghanistan.id, self.usa.id],
            'submit': 'Save + changes'
        })
        country, countries = self.getCountryAssignments(str(response))

        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.countries_assigned, countries)

    def test_user_can_save(self):
        self.user.is_superuser = False
        self.user.is_staff = False
        self.user.save()

        client = test.Client()
        client.login(username="tester", password='password')

        response = client.post(reverse('profile'), data={
            'title': '',
            'name': self.tola_user.name,
            'employee_number': self.tola_user.employee_number,
            'user': self.user.id,
            'language': 'fr',
            'submit': 'Save + changes'
        })
        country, countries = self.getCountryAssignments(str(response))

        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.countries_assigned, countries)

    @staticmethod
    def getCountryAssignments(form_html):

        soup = BeautifulSoup(form_html, 'html.parser')

        country_tags = soup.find('select', attrs={'id': 'id_country'})
        country = country_tags.find('option', attrs={'selected': True}).get('value')

        countries_tags = soup.find('select', attrs={'id': 'id_countries'})
        options = countries_tags.find_all('option', attrs={'selected': True})
        countries = set()
        for option in options:
            countries.add(int(option.get('value')))

        return country, countries
