import dataclasses, fnmatch, os.path, pathlib, re, requests, yaml

class DynalistToMarkdown:
    api_base = 'https://dynalist.io/api/v1/'

    def __init__(self, config,
        directory    = 'dynalist',
        overwrite    = False,
        http_session = requests
    ):
        self.directory    = directory
        self.overwrite    = overwrite
        self.http_session = http_session

        config = yaml.safe_load(config)
        self.api_key      = config['api_key']
        self.page_configs = [
            self.PageConfig(**page)
            for page in config['pages']
        ]

    def export(self):
        if not self.overwrite and os.path.exists(self.directory):
            raise Exception('Directory exists: ' + self.directory)

        self.fetch_files()
        self.process_files()

    def document_to_markdown(self, path, node_by_id, config, out):
        for context in self.traverse_nodes(node_by_id, 'root'):
            node    = context[-1]
            content = node['content']

            if config.include_notes:
                note = node.get('note', '')
                if note != '':
                    content += f' ({note})'

            if config.obsidian_internal_links:
                content = self.replace_markdown_links(content)

            if len(context) <= config.heading_depth:
                if len(context) > 1:
                    print(file=out)
 
                depth   = len(context)
                heading = '#' * depth
                print(f'{heading} {content}', file=out)
 
            else:
                indent = len(context) - config.heading_depth - 1
                indent = '\t' * indent
                print(f'{indent}- {content}', file=out)

    def fetch_files(self):
        response = self.request('file/list')
        files    = response['files']

        self.file_by_id   = self.index_nodes(files)
        self.root_file_id = response['root_file_id']

    def get_document(self, document_id):
        return self.request('doc/read', file_id=document_id)

    def page_config(self, page):
        config = None
        for page_config in self.page_configs:
            if page_config.match(page):
                if config:
                    config = config.merge(page_config)
                else:
                    config = page_config
        return config

    def process_files(self):
        for context in self.traverse_nodes(self.file_by_id, self.root_file_id):
            path = '/'.join(c['title'] for c in context[1:])
            node = context[-1]
            type = node['type']

            config = self.page_config(path)
            if type == 'document' and not config.ignore:
                self.process_document(path, node, config)

    def process_document(self, path, node, config):
        document_id = node['id']
        document    = self.get_document(document_id)
        nodes       = document['nodes']
        node_by_id  = self.index_nodes(nodes)

        print(f'{self.directory}/{path}')
        dir = os.path.dirname(path)
        pathlib.Path(self.directory, dir).mkdir(parents=True, exist_ok=True)
        with open(f'{self.directory}/{path}.md', 'w') as out:
            self.document_to_markdown(path, node_by_id, config, out)

    def request(self, api_path, **parameters):
        url = self.api_base + api_path

        response = self.http_session.post(url, json={'token': self.api_key, **parameters})
        if response.status_code != 200:
            raise Exception(f'Dynalist API error: {response.status_code}')

        result = response.json()
        if result.get('_code') == 'InvalidToken':
            raise Exception('Invalid API key: see https://dynalist.io/developer')
        return result

    def index_nodes(self, nodes):
        return {
            node['id']: node
            for node in nodes
        }

    def traverse_nodes(self, node_by_id, root_id):
        def traverse(context, id):
            node    = node_by_id[id]
            context = context + [node]
            yield context

            children = node.get('children')
            if children:
                for child_id in children:
                    yield from traverse(context, child_id)

        return traverse([], root_id)

    markdown_link_re = re.compile(r'\[([^\[]+)\]\(([^\)]+)\)')
    def replace_markdown_links(self, s):
        return re.sub(self.markdown_link_re, self.replace_obsidian_internal_links, s)

    # TODO: match fragment part and link to heading?
    dynalist_document_link_re = re.compile(r'^https://dynalist.io/d/([^#]+)')
    def replace_obsidian_internal_links(self, group):
        url       = group[2]
        url_group = self.dynalist_document_link_re.match(url)
        if url_group:
            document_id = url_group[1]
            document    = self.file_by_id.get(document_id)
            if document:
                text  = group[1]
                title = document['title']
                if text == title:
                    return f'[[{title}]]'
                else:
                    return f'[[{title}|{text}]]'
        return group[0]

    @dataclasses.dataclass
    class PageConfig:
        name                    : str
        heading_depth           : int  = None
        ignore                  : bool = None
        include_notes           : bool = None
        obsidian_internal_links : bool = None

        def match(self, page):
            return fnmatch.fnmatch(page, self.name)

        def merge(self, page_config):
            changes = {
                key: value
                for key, value in dataclasses.asdict(page_config).items()
                if value is not None
            }
            return dataclasses.replace(self, **changes)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description     = 'Export Dynalist to markdown',
        formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=40, width=79),
    )

    parser.add_argument(
        '--config',
        help     = 'Path to config file (default: ./dynalist_to_markdown.yaml)',
        default  = 'dynalist_to_markdown.yaml',
    )

    parser.add_argument(
        '--directory',
        help     = 'Directory for output (default: dynalist)',
        default  = 'dynalist',
    )

    parser.add_argument(
        '--overwrite',
        help     = 'Overwrite files in output directory',
        action   = 'store_true',
    )

    parser.add_argument(
        '--cache',
        help     = 'Enable requests cache (useful for development)',
        action   = 'store_true',
    )

    args = parser.parse_args()

    if args.cache:
        import requests_cache
        http_session = requests_cache.CachedSession(
            cache_name        = 'dynalist_exporter',
            allowable_methods = ('GET', 'POST')
        )
    else:
        http_session = requests

    with open(args.config) as config:
        exporter = DynalistToMarkdown(
            config       = config,
            directory    = args.directory,
            overwrite    = args.overwrite,
            http_session = http_session,
        )
        exporter.export()
