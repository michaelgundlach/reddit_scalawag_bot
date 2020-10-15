import re

def snippet(document, regex, bold_match=True):
    """Return a text snippet from |document| around |regex|, with the regex match itself bolded if |bold_match|.

    regex: Compiled regex object of the form f"\b{some phrase}\b", guaranteed to exist in |document|.
    """

    # Find the line that had the error.  We don't want the snippet to span multiple lines.
    line = line_containing_regex(document, regex)
    error_text = regex.search(line)[0]

    # Grab a few more words around the error_text.
    snippet_re = re.compile(r"(\b\S+\s+){0,5}" + error_text + "(\s+\S+){0,5}")
    snippet_match = snippet_re.search(line)
    snippet = snippet_match[0]

    # Put **bolding** around the error_text in the snippet.
    if bold_match:
        snippet = snippet.replace(regex.search(snippet)[0], f"**{error_text}**")

    # Put leading ellipses if the snippet doesn't start the line.
    if snippet_match.start() > 0:
        snippet = "..." + snippet

    # Put trailing ellipses if the snippet doesn't end the line.
    if snippet_match.end() != len(line):
        snippet = snippet + "..."

    return snippet


def swap(old, new, string):
    PH = "||PLACEHOLDER||"
    return string.replace(old, PH).replace(new, old).replace(PH, new)


def line_containing_regex(text, regex):
    """Return the line in text for which regex.search(line) is truthy.  One must match."""
    return [line for line in text.split('\n') if regex.search(line)][0]


