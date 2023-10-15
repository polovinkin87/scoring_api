import unittest
import api
import functools


def cases(case_list):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args):
            for case in case_list:
                new_args = args + (case,)
                try:
                    func(*new_args)
                except AssertionError:
                    print("Error in case: %s" % (case,))
                    raise
            return

        return wrapper

    return decorator


class BaseFieldTestCase(unittest.TestCase):
    def setUp(self):
        class ChildBaseField(api.BaseField):
            child_error = 'have error'
            is_error = True

            def clean(self):
                if self.is_error:
                    self.errors.append(self.child_error)

        self.field_class = ChildBaseField

    @cases([
        (False, []),
        (True, ['is require']),
    ])
    def test_require(self, case):
        required, error = case
        field = self.field_class(required=required)
        field._restore_errors()
        field.validate()
        self.assertEqual(field.errors, error)

    @cases([
        (True, [], []),
        (True, '', []),
        (False, [], ['is not nullable']),
        (False, '', ['is not nullable']),
    ])
    def test_nullable(self, case):
        nullable, value, error = case
        field = self.field_class(required=False, nullable=nullable)
        field.value = value
        field.validate()
        self.assertEqual(field.errors, error)

    @cases([
        (False, []),
        (True, ['have error']),
    ])
    def test_clean_method_error(self, case):
        status, error = case
        field = self.field_class(required=False, nullable=True)
        field.is_error = status
        field._restore_errors()
        field.value = 'test_text'
        field.validate()
        self.assertEqual(field.errors, error)


class CharFieldTestCase(unittest.TestCase):

    @cases([
        'test text',
        's'
    ])
    def test_valid_value(self, case):
        field = api.CharField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        ({'key': 'value'}, 'Is not a string'),
        (100, 'Is not a string'),
        (('string',), 'Is not a string'),
        ([1, 2, 3], 'Is not a string'),
        ({}, 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.CharField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class ArgumentsFieldTestCase(unittest.TestCase):

    @cases([
        {'test_key': 'test_value'},
        {'test_key': 'test_value', 'key2': 'value2'}
    ])
    def test_valid_value(self, case):
        field = api.ArgumentsField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        (100, 'Is not dict with arguments'),
        ('string', 'Is not dict with arguments'),
        (('string',), 'Is not dict with arguments'),
        ([1, 2, 3], 'Is not dict with arguments'),
        ({}, 'is not nullable'),
        ((), 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.ArgumentsField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class EmailFieldTestCase(unittest.TestCase):

    @cases([
        'email@mail.ru',
        '12345@mail.com',
    ])
    def test_valid_value(self, case):
        field = api.EmailField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        ('test', 'Is not email'),
        ('email_mail.ru', 'Is not email'),
        (100, 'Is not a string'),
        (('text',), 'Is not a string'),
        ([1, 2, 3], 'Is not a string'),
        ({}, 'is not nullable'),
        ((), 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.EmailField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class PhoneFieldTestCase(unittest.TestCase):
    @cases([
        '79287654321',
        79281234567,
    ])
    def test_valid_value(self, case):
        field = api.PhoneField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        ('866666666666666', 'Is not phone number'),
        ('7928426_135', 'Is not phone number'),
        (7928426135., 'Is not phone number'),
        ([1, 2, 3], 'Is not phone number'),
        ({}, 'is not nullable'),
        ((), 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.PhoneField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class DateFieldTestCase(unittest.TestCase):

    @cases([
        '13.02.2023',
        '1.1.2000',
    ])
    def test_valid_value(self, case):
        field = api.DateField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        ('13.02.23', 'Is note date'),
        ('1.1.20', 'Is note date'),
        ('10.2023', 'Is note date'),
        ('2023.2010.2021', 'Is note date'),
        (13.2023, 'Is note date'),
        ([1, 2, 3], 'Is note date'),
        ({}, 'is not nullable'),
        ((), 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.DateField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class BirthDayFieldTestCase(unittest.TestCase):

    @cases([
        '28.10.2014',
        '30.11.1953',
    ])
    def test_valid_value(self, case):
        field = api.BirthDayField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        ('30.06.1941', 'Not a birthday'),
        ('01.01.1000', 'Not a birthday'),
        ((), 'is not nullable'),
        ({}, 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.BirthDayField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class GenderFieldTestCase(unittest.TestCase):

    @cases([
        0,
        1,
        2,
    ])
    def test_valid_value(self, case):
        field = api.GenderField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        (3, 'is not a gender number'),
        ('3', 'is not a gender number'),
        ('30.06.1941', 'is not a gender number'),
        ('test case', 'is not a gender number'),
        ('1.1.23', 'is not a gender number'),
        ({'test_key': 'test_value'}, 'is not a gender number'),
        ([1], 'is not a gender number'),
        (13.2023, 'is not a gender number'),
        ([1, 2, 3], 'is not a gender number'),
        ({}, 'is not nullable'),
        ((), 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.GenderField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class ClientIDsFieldTestCase(unittest.TestCase):

    @cases([
        [0],
        [1, 3, 5, 6],
        [2],
    ])
    def test_valid_value(self, case):
        field = api.ClientIDsField(required=True, nullable=False)
        field.value = case
        field.validate()
        self.assertFalse(field.errors)

    @cases([
        ([1, (2, 3)], 'Is not list of client ids'),
        (3, 'Is not list of client ids'),
        ('3', 'Is not list of client ids'),
        ('30.06.1941', 'Is not list of client ids'),
        ('test case', 'Is not list of client ids'),
        ('1.1.23', 'Is not list of client ids'),
        ({'test_key': 'test_value'}, 'Is not list of client ids'),
        (13.2023, 'Is not list of client ids'),
        ((), 'is not nullable'),
        ([], 'is not nullable'),
        ({}, 'is not nullable'),
    ])
    def test_invalid_value_(self, case):
        value, error = case
        field = api.ClientIDsField(required=True, nullable=False)
        field.value = value
        field.validate()
        self.assertEquals(field.errors, [error])


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments":
            {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "123",
         "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments":
            {}},
        {"account": "horns&hoofs", "login": "user", "method": "clients_interests",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"client_ids": [1, 2, 3, 4], "date": "13.02.2023"}}
    ])
    def test_bad_auth(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {"account": "horns&hoofs", "login": "user", "method": "clients_interests",
         "arguments": {"client_ids": [1, 2, 3, 4], "date": "13.02.2023"}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score",
         "arguments": {}},
    ])
    def test_token_require(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {"account": "horns&hoofs", "login": "vasya", "method": "get",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {}},
        {"account": "horns&hoofs", "login": "vasya", "method": "post",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {}},
    ])
    def test_method_not_found(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.NOT_FOUND, code)


class TestSuiteWithStore(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = api.Store(api.DEFAULT_CACHE_CLIENT, api.DEFAULT_CACHE_ADDRESS)

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    @cases([
        {"account": "horns&hoofs", "login": "vasya", "method": "online_score",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"phone": "79174002042", "email": "vasya@otus.ru", "first_name": "Вася",
                       "last_name": "Щупкин", "birthday": "01.01.1990", "gender": 2}},
        {"account": "horns&hoofs", "login": "vasya", "method": "online_score",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"phone": "79174002042", "email": "vasya@otus.ru", }},
        {"account": "horns&hoofs", "login": "vasya", "method": "online_score",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"birthday": "01.01.1990", "gender": 2}},
        {"account": "horns&hoofs", "login": "vasya", "method": "online_score",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"first_name": "Вася", "last_name": "Щупкин"}},
    ])
    def test_valid_request(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.OK, code)

    @cases([
        {"account": "horns&hoofs", "login": "vasya", "method": "online_score",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"phone": "79174002042", "email": "vasya@otus.ru", "first_name": "Вася",
                       "last_name": "Щупкин", "birthday": "01.01.1990", "gender": 10}},
        {"account": "horns&hoofs", "login": "vasya", "method": "online_score",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"phone": "79175002040", "last_name": "Щупкин", "gender": 10}},
        {"account": "horns&hoofs", "login": "vasya", "method": "online_score",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {}},
        {"account": "horns&hoofs", "login": "vasya", "method": "clients_interests",
         "token": "7b1a275ce1e204b0c0a43c23c4e437eb4c5e731948698ef8ff3d66b0952e2154d4ad3ffe02f914cf5b2cca2fe57a952b802a5d39e6b6da5e329f33f85d71fbcb",
         "arguments": {"client_ids": 10, "date": "13.02.2023"}},
    ])
    def test_invalid_request(self, request):
        _, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)


if __name__ == "__main__":
    unittest.main()
