#!/usr/bin/env python3
def generate_pytest_decorator_input(var_order, ok_test_parameters, ko_test_parameters):
    test_vars = ""
    values_list = []

    # OK tests
    number_of_ok_tests = 0
    for k, v in ok_test_parameters.items():
        number_of_ok_tests = max(number_of_ok_tests, len(v))

    for var in var_order:
        test_vars += var + ","
    test_vars += "expected"

    for idx in range(number_of_ok_tests):
        test_value_tuple = tuple()

        for var in var_order:
            test_value_tuple += (ok_test_parameters[var][idx % len(ok_test_parameters[var])],)
        test_value_tuple += (0,)

        values_list.append(test_value_tuple)

    # KO tests
    test_parameters_ko_list = []
    for k, v in ko_test_parameters.items():
        for value in v:
            test_parameters_ko_list.append([k, value])
    number_of_ko_tests = len(test_parameters_ko_list)

    for idx in range(number_of_ko_tests):
        test_value_tuple = tuple()

        for var in var_order:
            if var == test_parameters_ko_list[idx][0]:
                test_value_tuple += (test_parameters_ko_list[idx][1],)
            else:
                test_value_tuple += (ok_test_parameters[var][idx % len(ok_test_parameters[var])],)

        test_value_tuple += (1,)

        values_list.append(test_value_tuple)

    return test_vars, values_list