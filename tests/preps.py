from ongtrum.annotation import prep


@prep(scope='session')
def session_prep():
    return 'Session Prep'


@prep(scope='class')
def class_prep():
    return 'Class Prep'


@prep(scope='method')
def method_prep():
    return 'Method Prep'
