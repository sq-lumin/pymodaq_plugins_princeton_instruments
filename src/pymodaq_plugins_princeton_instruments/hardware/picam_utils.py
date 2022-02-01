def normalise_name(name):
    return name.replace(' ' ,'_').lower()

def define_pymodaq_pyqt_parameter(parameter):
    # Get basic parameter attributes
    p_title = parameter.name
    p_fmt_name = normalise_name(parameter.name)
    p_type = None
    p_value = parameter.get_value(enum_as_str=True)
    p_limits = None
    p_readonly = not parameter.writable

    # Here it gets slightly intricate.
    # The parameters might be int,large int or float with a fixed number of
    # allowed values, in which case it is dealt as a list with some allowed values
    if parameter.kind in ['Integer' ,'Large Integer']:
        # We recognize them because they have labels defined, i.e. the label dict is non-empty
        if parameter.labels != {}:
            p_type = 'list'
            p_limits = list(parameter.labels.values())
        else:
            p_type = 'int'
            # There might be limits though
            if parameter.cons_type == "Range" and parameter.cons_permanent == True:
                p_limits = [parameter.min ,parameter.max]
            else:
                p_limits = None
    # The story is similar for floats
    elif parameter.kind == 'Floating Point':
        # We recognize them because they have labels defined, i.e. the label dict is non-empty
        if parameter.labels != {}:
            p_type = 'list'
            p_limits = list(parameter.labels.values())
        else:
            p_type = 'float'
            # There might be limits though
            if parameter.cons_type == "Range" and parameter.cons_permanent == True:
                p_limits = [parameter.min ,parameter.max]
            else:
                p_limits = None
    # Boolean is easy
    elif parameter.kind == 'Boolean':
        p_type = 'bool'
    # Enumeration is ok
    elif parameter.kind == 'Enumeration':
        p_type = 'list'
        p_limits = list(parameter.labels.keys())  # Always str
    # ROIs is special
    elif parameter.kind == 'ROIs':
        return  # Return None
    else:
        raise ValueError

    p_dict = {'title': p_title,
              'name': p_fmt_name,
              'type': p_type,
              'value': p_value,
              'readonly': p_readonly}

    if p_limits != None:
        p_dict.update({'limits' : p_limits})

    return p_dict