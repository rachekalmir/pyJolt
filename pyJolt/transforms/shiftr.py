from collections import defaultdict

l = lambda: defaultdict(l)


def shift(spec, data):
    output = process_shift(spec, data)

    return output


def process_shift(spec, data):
    result = l()
    for key, value in spec.items():
        if type(value) is dict:
            if key in data:
                result.update(process_shift(spec[key], data[key]))
            else:
                # key doesn't exist in data
                pass
        else:
            p = result
            for ikey in value.split('.')[:-1]:
                p = p[ikey]
            p[value.split('.')[-1]] = data[key]
    return result
