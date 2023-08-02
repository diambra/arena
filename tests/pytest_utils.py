#!/usr/bin/env python3
from diambra.arena.utils.engine_mock import DiambraEngineMock

def generate_pytest_decorator_input(var_order, test_parameters, outcome):

    test_vars = ""
    values_list = []

    number_of_tests = 0
    for k, v in test_parameters.items():
        number_of_tests = max(number_of_tests, len(v))

    for var in var_order:
        test_vars += var + ","
    test_vars += "expected"

    for idx in range(number_of_tests):

        test_value_tuple = tuple()

        for var in var_order:
            test_value_tuple += (test_parameters[var][idx % len(test_parameters[var])],)
        test_value_tuple += (outcome,)

        values_list.append(test_value_tuple)

    return test_vars, values_list

def load_mocker(mocker):
    diambra_engine_mock = DiambraEngineMock()

    mocker.patch("diambra.arena.engine.interface.DiambraEngine.__init__", diambra_engine_mock.mock__init__)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.env_init", diambra_engine_mock.mock_env_init)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.reset", diambra_engine_mock.mock_reset)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.step", diambra_engine_mock.mock_step)
    mocker.patch("diambra.arena.engine.interface.DiambraEngine.close", diambra_engine_mock.mock_close)