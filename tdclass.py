import certifi
from json import loads as json_loads
from urllib3 import PoolManager


class TasteDive():
    """
    This allows you to connect to Tastedive and handle requests for
    similar things.
    """

    def __init__(self, key=None):
        self.key = key
        self.request_url = 'https://tastedive.com/api/similar'
        self.http = PoolManager(
            cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

    def get_similar(self, query=None, q_type='', info=1, verbose=1, limit=20):
        """
        It gets similar things based on the query.
        """
        operators = ["band:", "movie:", "show:", "book:", "author:", "game:"]
        # tastedive wants us to use operators without spaces.
        # it should be operator:item instead of operator: item. so,
        # we'll check it for spaces. if there is, remove it
        for operator in operators:
            if operator + ' ' in query:
                query = query.replace(operator + ' ', operator)

        # args for the url
        args = {
            'k': self.key,
            'q': query,
            'type': q_type,
            'info': 1 if info is True else 0,
            'verbose': 1 if verbose is True else 0,
            'limit': limit
        }
        # q_types = music, movies, shows, books, authors, games
        try:
            results = self.http.request('GET', self.request_url, fields=args)
            results = json_loads(results.data.decode('utf-8'))

            similars = results['Similar']
            info, result = similars['Info'], similars['Results']
            if len(result) < 1 and info[0]['Type'] == 'unknown':
                error_message = '⌛️ Loading..\n🤔 I found nothing'
                raise ValueError(error_message)
            elif len(result) < 1:
                error_message = (
                    '🤔 I found nothing..'
                    '\n\nIf your result type is not "all", it may be '
                    'the reason behind this.'
                )
                raise ValueError(error_message)
            return (info, result)
        except ValueError as e:
            raise e
        except Exception as e:
            raise KeyError('No result found in the content.')

        return False

    def prettify(self, info, result):
        results = ''
        types = {
            'music': '🎤', 'movie': '🎬', 'show': '📺',
            'book': '📖', 'author': '👤', 'game': '🕹',
        }

        for tip, value in enumerate([info, result], 1):
            if tip == 1:
                results += '🔘 <b>Your Choices:</b>\n'
                results += 'These are your identified choices.\n\n'
            elif tip == 2:
                results += '💎 <b>SIMILAR THINGS:</b>\n'
                results += ('These are the similar things based on your '
                            'choices.\n\n')

            for num, item in enumerate(value, 1):
                name = item['Name']
                category = types[item['Type']]
                w_teaser = item['wTeaser'][:120]
                w_url = item['wUrl']
                y_url = item['yUrl']
                # y_id = item['yID']

                results += (
                    "<b>{} - {}</b> {}\n"
                    "{}\n"
                    ).format(
                        num, name, category, w_teaser.strip())
                if w_url:
                    results += "<a href=\"{}\">{}</a>".format(w_url, 'Wiki')

                if y_url:
                    results += " - <a href=\"{}\">{}</a>\n\n".\
                        format(y_url, 'YouTube')
                else:
                    results += '\n\n'

            results += '─────\n\n'

        results += ('<b>Did you like it?</b>\n'
                    'Please give me 5 stars! 🤓')

        return results
