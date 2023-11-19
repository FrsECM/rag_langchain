from datetime import datetime
DATE_FORMATS=['%Y-%m-%dT%H:%M:%S.%f%z','%Y-%m-%d']

def parse_date(date):
    if date is None:
        return None
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(date, date_format)
        except ValueError:
            pass
    raise Exception(f'Unparsable date {date} with dateformat {DATE_FORMATS}')

def str_date(date:datetime):
    if date is not None:
        return date.strftime('%Y-%m-%d')
    else:
        return 'None'
def force_type(input):
    if isinstance(input,(float,int,bool,str)):
        return input
    if input is None:
        return ''
    else:
        raise Exception('type incompatible with vector database...')
