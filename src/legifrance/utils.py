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
