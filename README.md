# Dynalist to Markdown

This is a script that exports Dynalist to Markdown.  While it does generate
standard Markdown, it was designed to export from Dynalist to Obsidian, and so
it supports some Obsidian-specific features, such as internal links.

## Installation

The script requires Python 3, as well as a few python modules, such as
`requests` and `pyyaml`.  I recommend creating a Python `venv` and installing
modules in this environment.  This details of how to do this depend on your
platform.  For example:

```
python3 -mvenv .venv
. .venv/bin/activate
pip install requests pyyaml
```

## Configuration

Navigate to the [Dynalist developer page](https://dynalist.io/developer) and
Generate a secret token.  Copy this secret token to your clipboard.

Copy the `dynalist_to_markdown.yaml.example` file to
`dynalist_to_markdown.yaml`, and open `dynalist_to_markdown.yaml` with a text
editor.  Replace the `<YOUR API KEY HERE>` text with the secret token you just
copied.

Additionally, you can define the configuration on a per-page basis.  Since
Dynalist is an outliner, each document is just a big nested list.  While we
could just convert this into a big nested Markdown list, that's probably not
what you want.

[Note: A major weakness of the current implementation is that it only
generates headings and list items -- never paragraphs.  Hopefully a future
version will provide this functionality.]

Edit the `pages` section of the `dynalist_to_markdown.yaml` config file,
using the following configuration settings.

| Key                       | Description                                    |
| ------------------------- | ---------------------------------------------- |
| `name`                    | The name of the page to which these configuration settings apply.  This can be a pattern, using a `*` to match any sequence of characters (or `?` to match a single character). |
| `heading_depth`           | The number of levels of headings to generate. |
| `ignore`                  | Ignore this page -- don't generate Markdown for it. |
| `include_notes`           | Whether to include the "notes" section of a Dynalist item. |
| `obsidian_internal_links` | Whether to convert internal links to Obsidian-style notation (e.g. `[[Link]]`) |
| `page_header`             | Whether to generate a top-level header with the page name.  You may want to enable this if you are not using the "Show inline title" option in Obsidian. |

## Usage

Once you've created the configuration file, you just simply run the script.  There are
a few optional command-line settings, however:

```
$ python dynalist_to_markdown.py -h
usage: dynalist_to_markdown.py [-h] [--config CONFIG] [--directory DIRECTORY]
                               [--overwrite] [--cache]

Export Dynalist to markdown

optional arguments:
  -h, --help             show this help message and exit
  --config CONFIG        Path to config file (default:
                         ./dynalist_to_markdown.yaml)
  --directory DIRECTORY  Directory for output (default: dynalist)
  --overwrite            Overwrite files in output directory
  --cache                Enable requests cache (useful for development)
```

By default, the script will create a folder called `dynalist` with all of the
generated Markdown files.  To change this folder name, use the `--directory`
option.

If you plan to run the script multiple times (e.g. tweaking the configuration
each time, or modifying the Python script), you may want to enable request
caching.  This enables you to run the script subsequent times without hitting
the Dynalist API each time.  To do this, install the `requests_cache` module
and use the `--cache option`:

```
pip install requests_cache
python dynalist_to_markdown.py --cache
```
