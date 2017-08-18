import argparse

delete_request = 'http://{host}:{port}/solr/{collection}/update?stream.body=<delete><query>{query}</query></delete>&commit=true'
select_request = 'http://{host}:{port}/solr/{collection}/select?q={query}&rows=0&wt=json'


def create_arguments():
    parser = argparse.ArgumentParser(prog='delete_dataset', add_help=True, description='Delete records from SOLR')

    parser.add_argument('--collection', help='Collection name', required=True)
    parser.add_argument('--query', help='Query - records matching will be deleted!')
    parser.add_argument('--server', help='SOLR hostname', required=True)
    parser.add_argument('--port', help='SOLR port', default=8983)
    parser.add_argument('--confirm', action='store_true', default=False, help='Confirm you want to proceed')

    return parser


def main():
    parser = create_arguments()
    args = parser.parse_args()

    d = {
        'host': args.server,
        'collection': args.collection,
        'port': args.port,
        'query': args.query
    }

    if args.confirm:
        print('Your delete URL is:')
        print(delete_request.format(**d))
        print('Run the command yourself if you really want to!')

    else:
        print("Check what you're going to delete first!")
        print(select_request.format(**d))

if __name__ == '__main__':
    main()
