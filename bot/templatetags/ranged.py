from django import template
register = template.Library()

@register.filter(name='ranged')
def ranged(current,last):

    maximum = last[-1]
    minimum = 1
    lowerbound = current
    upperbound = current

    for i in range(3):
        if lowerbound - 1 >= minimum :
            lowerbound = lowerbound - 1
        else:
            break
    
    for i in range(3):
        if upperbound + 1 <= maximum :
            upperbound = upperbound + 1
        else:
            break

    
    return range(lowerbound,upperbound+1)