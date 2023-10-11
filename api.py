#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
from scoring import get_score, get_interests

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseField:
    __metaclass__ = abc.ABCMeta
    require_error = "is require"
    nullable_error = "is not nullable"
    value = None
    errors = []

    def __init__(self, required, nullable=False):
        self.required = required
        self.nullable = nullable

    def __cmp__(self, other):
        if self.value == other:
            return 0
        if self.value > other:
            return 1
        return -1

    def __add__(self, other):
        return self.__str__() + str(other)

    def __str__(self):
        return self.value

    def __set__(self, instance, value):
        self.value = value

    def validate(self):
        self._restore_errors()
        if self.value is None:
            self.clean_required()
        elif not self.value and not isinstance(self.value, int):
            self.clean_nullable()
        else:
            self.clean()

    def _restore_errors(self):
        self.errors = []

    def clean_required(self):
        if self.required:
            self.errors.append(self.require_error)

    def clean_nullable(self):
        if not self.nullable:
            self.errors.append(self.nullable_error)

    @abc.abstractmethod
    def clean(self):
        pass


class CharField(BaseField):
    char_error = "Is not a string"

    def clean(self):
        if not isinstance(self.value, str):
            self.errors.append(self.char_error)


class ArgumentsField(BaseField):
    arguments_error = 'Is not dict with arguments'

    def clean(self):
        if not isinstance(self.value, dict):
            self.errors.append(self.arguments_error)


class EmailField(CharField):
    email_error = "Is not email"

    def clean(self):
        super().clean()
        if isinstance(self.value, str):
            if '@' not in self.value:
                self.errors.append(self.email_error)


class PhoneField(BaseField):
    phone_error = 'Is not phone number'
    phone_template = r"7\d{10}"

    def clean(self):
        value = self.value
        if isinstance(value, int):
            value = str(value)
        if isinstance(value, str):
            if not re.match(self.phone_template, value):
                self.errors.append(self.phone_error)
        else:
            self.errors.append(self.phone_error)


class DateField(BaseField):
    data_error = 'Is note date'

    def clean(self):
        try:
            date_string = self.value
            self.value = datetime.datetime.strptime(date_string, '%d.%m.%Y').date()
        except (ValueError, TypeError):
            self.errors.append(self.data_error)


class BirthDayField(DateField):
    birthday_error = 'Not a birthday'

    def clean(self):
        super().clean()
        try:
            if self.value < datetime.datetime.now().date() - datetime.timedelta(days=365 * 70):
                self.errors.append(self.birthday_error)
        except (ValueError, TypeError):
            self.errors.append(self.birthday_error)


class GenderField(BaseField):
    gender_error = 'is not a gender number'

    def clean(self):
        if not isinstance(self.value, int) or self.value not in (UNKNOWN, MALE, FEMALE):
            self.errors.append(self.gender_error)


class ClientIDsField(BaseField):
    client_id_error = 'Is not list of client ids'

    def clean(self):
        if not isinstance(self.value, list):
            self.errors.append(self.client_id_error)
        else:
            for element in self.value:
                if not isinstance(element, int):
                    self.errors.append(self.client_id_error)
                    break


class BaseRequest:
    __metaclass__ = abc.ABCMeta
    fields_with_validation = []

    def __init__(self):
        self.errors = {}

    def validate_fields(self):
        for field_name in self.fields_with_validation:
            field = getattr(self, field_name)
            field.validate()
            if field.errors:
                self.errors[field_name] = field.errors

    def get_data(self):
        fields = {}
        for field_name in self.fields_with_validation:
            field = getattr(self, field_name)
            fields[field_name] = field.value
        return fields

    def get_errors(self):
        errors_list = []
        for key, value in self.errors.items():
            if value:
                error_value = ", ".join(value)
                errors_list.append(f"{key}: {error_value}")
        errors_str = "; ".join(errors_list)
        return f"{errors_str}."

    @abc.abstractmethod
    def is_valid(self):
        pass


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)
    fields_with_validation = ['client_ids', 'date']

    def __init__(self, kwargs):
        super().__init__()
        self.client_ids = kwargs.get('client_ids', None)
        self.date = kwargs.get('date', None)

    def is_valid(self):
        self.validate_fields()
        if self.errors:
            return False
        return True


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)
    validate_groups = (
        ('first_name', 'last_name'),
        ('phone', 'email'),
        ('gender', 'birthday'),
    )
    fields_with_validation = ['first_name', 'last_name', 'email', 'phone', 'birthday', 'gender']

    def __init__(self, kwargs):
        super().__init__()
        self.first_name = kwargs.get('first_name', None)
        self.last_name = kwargs.get('last_name', None)
        self.email = kwargs.get('email', None)
        self.phone = kwargs.get('phone', None)
        self.birthday = kwargs.get('birthday', None)
        self.gender = kwargs.get('gender', None)
        self.not_null_fields = []

    def is_valid(self):
        self.validate_fields()
        if self.errors:
            return False
        self.find_not_null_fields_name()
        for validate_group in self.validate_groups:
            if (validate_group[0] in self.not_null_fields
                    and validate_group[1] in self.not_null_fields):
                return True
        return False

    def find_not_null_fields_name(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, BaseField):
                if attr.value is not None:
                    self.not_null_fields.append(attr_name)


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)
    fields_with_validation = ['account', 'login', 'token', 'arguments', 'method']

    def __init__(self, kwargs):
        super().__init__()
        self.account = kwargs.get('account', None)
        self.login = kwargs.get('login', None)
        self.token = kwargs.get('token', None)
        self.arguments = kwargs.get('arguments', None)
        self.method = kwargs.get('method', None)

    def is_valid(self):
        self.validate_fields()
        if self.errors:
            return False
        return True

    @property
    def is_admin(self):
        return self.login.value == ADMIN_LOGIN


def check_auth(request):
    if request.login.value == ADMIN_LOGIN:
        temp = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        digest = hashlib.sha512(temp.encode('utf-8')).hexdigest()
    else:
        temp = request.account + request.login + SALT
        digest = hashlib.sha512(temp.encode('utf-8')).hexdigest()
    if digest == request.token.value:
        return True
    return False


def online_score_handler(arguments, is_admin, ctx, store):
    online_score_request = OnlineScoreRequest(arguments)
    if is_admin:
        code = OK
        response = {'score': 42}
    elif online_score_request.is_valid():
        code = OK
        attrs = online_score_request.get_data()
        score = get_score(store, **attrs)
        response = {'score': score}
    else:
        code = INVALID_REQUEST
        response = online_score_request.get_errors()
    ctx['has'] = online_score_request.not_null_fields
    return response, code


def clients_interests_handler(arguments, is_admin, ctx, store):
    clients_interests_request = ClientsInterestsRequest(arguments)
    if clients_interests_request.is_valid():
        code = OK
        response = {}
        for client_id in clients_interests_request.client_ids.value:
            response[client_id] = get_interests(store, client_id)
    else:
        response, code = clients_interests_request.get_errors(), INVALID_REQUEST
    try:
        ctx['nclients'] = len(clients_interests_request.client_ids.value)
    except TypeError:
        ctx['nclients'] = 0
    return response, code


def method_handler(request, ctx, store):
    handler_router = {
        'online_score': online_score_handler,
        'clients_interests': clients_interests_handler
    }
    body = request['body']
    method_request = MethodRequest(body)
    if method_request.is_valid():
        if check_auth(method_request):
            if method_request.method.value in handler_router:
                response, code = handler_router[method_request.method.value](
                    method_request.arguments.value,
                    method_request.is_admin,
                    ctx,
                    store
                )
            else:
                response, code = 'method not found', NOT_FOUND
        else:
            response, code = 'invalid token', FORBIDDEN
    else:
        response, code = method_request.get_errors(), INVALID_REQUEST
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler,
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = (self.rfile.read(int(self.headers['Content-Length'])))
            request = json.loads(data_string)
        except Exception as err:
            logging.exception(err)
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info(f"{self.path}: {data_string} {context['request_id']}")
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers}, context, self.store)
                except Exception as err:
                    logging.exception(err)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            data = {"response": response, "code": code}
        else:
            data = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(data)
        logging.info(context)
        self.wfile.write(json.dumps(data).encode('utf-8'))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info(f"Starting server at {opts.port}")
    try:
        server.serve_forever()
    except Exception as error:
        logging.exception(f"Unexpected error: {error}")
    server.server_close()
