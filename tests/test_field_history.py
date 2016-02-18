#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
from unittest.case import skip

from django.test import TestCase
from django.utils import six
from field_history.models import FieldHistory

from .models import Human, Person, Pet, Owner


class TestFieldHistory(TestCase):

    def test_new_object_creates_field_history(self):
        # No FieldHistory objects yet
        self.assertEqual(FieldHistory.objects.count(), 0)

        person = Person.objects.create(name='Initial Name')

        # Creating an object will make one
        self.assertEqual(FieldHistory.objects.count(), 1)

        # This object has some fields on it
        history = FieldHistory.objects.get()
        self.assertEqual(history.object, person)
        self.assertEqual(history.field_name, 'name')
        self.assertEqual(history.field_value, 'Initial Name')
        self.assertIsNotNone(history.date_created)

    def test_updated_object_creates_additional_field_history(self):
        person = Person.objects.create(name='Initial Name')

        # Updating that particular field creates a new FieldHistory
        person.name = 'Updated Name'
        person.save()
        self.assertEqual(FieldHistory.objects.count(), 2)

        histories = FieldHistory.objects.get_for_model_and_field(person, 'name')

        updated_history = histories.order_by('-date_created').first()
        self.assertEqual(updated_history.object, person)
        self.assertEqual(updated_history.field_name, 'name')
        self.assertEqual(updated_history.field_value, 'Updated Name')
        self.assertIsNotNone(updated_history.date_created)

        # One more time for good measure
        person.name = 'Updated Again'
        person.save()
        self.assertEqual(FieldHistory.objects.count(), 3)

        histories = FieldHistory.objects.get_for_model_and_field(person, 'name')

        third_history = histories.order_by('-date_created').first()
        self.assertEqual(third_history.object, person)
        self.assertEqual(third_history.field_name, 'name')
        self.assertEqual(third_history.field_value, 'Updated Again')
        self.assertIsNotNone(third_history.date_created)

    def test_model_field_history_attribute_returns_all_histories(self):
        person = Person.objects.create(name='Initial Name')

        histories = FieldHistory.objects.get_for_model_and_field(person, 'name')

        six.assertCountEqual(self, list(person.field_history), list(histories))

    def test_model_has_get_field_history_method(self):
        person = Person.objects.create(name='Initial Name')

        history = FieldHistory.objects.get()

        # Or using the {field_name}_history property added to your model
        six.assertCountEqual(self, list(person.get_name_history()), [history])

    def test_field_history_is_not_created_if_field_value_did_not_change(self):
        person = Person.objects.create(name='Initial Name')

        self.assertEqual(FieldHistory.objects.count(), 1)

        # The value of person did not change, so don't create a new FieldHistory
        person.name = 'Initial Name'
        person.save()

        self.assertEqual(FieldHistory.objects.count(), 1)

    def test_field_history_works_with_integer_field(self):
        human = Human.objects.create(age=18)

        self.assertEqual(human.get_age_history().count(), 1)
        history = human.get_age_history()[0]

        self.assertEqual(history.object, human)
        self.assertEqual(history.field_name, 'age')
        self.assertEqual(history.field_value, 18)
        self.assertIsNotNone(history.date_created)

    def test_field_history_works_with_decimal_field(self):
        human = Human.objects.create(body_temp=98.6)

        self.assertEqual(human.get_body_temp_history().count(), 1)
        history = human.get_body_temp_history()[0]

        self.assertEqual(history.object, human)
        self.assertEqual(history.field_name, 'body_temp')
        self.assertEqual(history.field_value, 98.6)
        self.assertIsNotNone(history.date_created)

    def test_field_history_works_with_boolean_field(self):
        human = Human.objects.create(is_female=True)

        self.assertEqual(human.get_is_female_history().count(), 1)
        history = human.get_is_female_history()[0]

        self.assertEqual(history.object, human)
        self.assertEqual(history.field_name, 'is_female')
        self.assertEqual(history.field_value, True)
        self.assertIsNotNone(history.date_created)

    def test_field_history_works_with_date_field(self):
        birth_date = datetime.date(1991, 11, 6)
        human = Human.objects.create(birth_date=birth_date)

        self.assertEqual(human.get_birth_date_history().count(), 1)
        history = human.get_birth_date_history()[0]

        self.assertEqual(history.object, human)
        self.assertEqual(history.field_name, 'birth_date')
        self.assertEqual(history.field_value, birth_date)
        self.assertIsNotNone(history.date_created)

    def test_field_history_tracks_multiple_fields_changed_at_same_time(self):
        human = Human.objects.create(
            birth_date=datetime.date(1991, 11, 6),
            is_female=True,
            body_temp=98.6,
            age=18,
        )

        self.assertEqual(FieldHistory.objects.count(), 4)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'birth_date').count(), 1)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'is_female').count(), 1)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'body_temp').count(), 1)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'age').count(), 1)

        human.birth_date = datetime.date(1992, 11, 6)
        human.is_female = False
        human.body_temp = 100.0
        human.age = 21
        human.save()

        self.assertEqual(FieldHistory.objects.count(), 8)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'birth_date').count(), 2)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'is_female').count(), 2)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'body_temp').count(), 2)
        self.assertEqual(FieldHistory.objects.get_for_model_and_field(human, 'age').count(), 2)

    def test_field_history_works_with_foreign_key_field(self):
        pet = Pet.objects.create(name='Garfield')
        owner = Owner.objects.create(name='Jon', pet=pet)

        self.assertEqual(owner.get_pet_history().count(), 1)
        history = owner.get_pet_history()[0]

        self.assertEqual(history.object, owner)
        self.assertEqual(history.field_name, 'pet')
        self.assertEqual(history.field_value, pet)
        self.assertIsNotNone(history.date_created)

    def test_field_history_works_with_field_set_to_None(self):
        owner = Owner.objects.create(pet=None)

        history = owner.get_pet_history()[0]

        self.assertEqual(history.object, owner)
        self.assertEqual(history.field_name, 'pet')
        self.assertEqual(history.field_value, None)
