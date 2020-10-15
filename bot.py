import logging
import sys
import re
import time

from itertools import chain

import praw

from delayed_stream import delayed_stream
from textutils import snippet, swap, line_containing_regex

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stderr))


DELAY_SECONDS = 360  # Minimum age of comments we reply to

REPLY_TEMPLATE = """> {snippet}

I think you want "{fixed_error}", not "{error}".  As [Strongbad's song](https://www.youtube.com/watch?v=yc2udEpyPpU) says,

_If you want it to be possessive, it's just "I-T-S"_\\
_But if it's supposed to be a contraction then it's "I-T-apostrophe-S"_\\
_^^...Scalawag^^_

---

^^I'm ^^a ^^bot by ^^Michael ^^Gundlach.  ^^Please ^^don't ^^hurt ^^me, ^^beep ^^boop!  ^^[code](https://github.com/michaelgundlach/reddit_scalawag_bot)
"""

def phrases_with_forgotten_apostrophe():
    for word in "not a ok the really".split():
        yield f"its {word}"

def phrases_with_extra_apostrophe():
    for preposition in "of with on in for under above around inside".split():
        yield f"{preposition} it's"

ERRORS = {}  # Maps regex to (phrase, error type)
for phrase in phrases_with_forgotten_apostrophe():
    ERRORS[re.compile(rf"\b{phrase}\b", flags=re.I)] = (phrase, "forgotten")
for phrase in phrases_with_extra_apostrophe():
    ERRORS[re.compile(rf"\b{phrase}\b", flags=re.I)] = (phrase, "extra")


def swap_its(error_text):
    """Replace it's with its and vice versa in error_text."""
    for word in "it's IT'S It's".split():
        error_text = swap(word, word.replace("'", ""), error_text)
    return error_text


def not_worth_correcting(comment, error_regex):
    """True if our particular grammar issue isn't the commenter's main concern..."""
    if comment.body == comment.body.lower():  # Everything is in lower case; it may be a stylistic choice
        return True
    if line_containing_regex(comment.body, error_regex).startswith('>'):  # The error was in quoted text
        return True
    if comment.author.name == 'scalawag_bot':  # No recursion, thank you
        return True


def should_reply(comment):
    for error_regex in ERRORS:
        if error_regex.search(comment.body):
            logger.debug(f"match: {error_regex.search(comment.body)[0]}")
            if not_worth_correcting(comment, error_regex):
                logger.error(f"Skipping comment:\n---\n{comment.body}\n---")
            else:
                return error_regex


def reply_text(comment, error_regex):
    """The text to send in response to the comment matching |error_regex|."""
    matched_phrase = error_regex.search(comment.body)[0]
    corrected_phrase = swap_its(matched_phrase)
    snippet_text = snippet(comment.body, error_regex)
    return REPLY_TEMPLATE.format(snippet=snippet_text, fixed_error=corrected_phrase, error=matched_phrase)


def reply_to_comment(comment):
    error_regex = should_reply(comment)
    reply = reply_text(comment, error_regex)
    logger.debug(f"comment line in {comment.subreddit.display_name}: {line_containing_regex(comment.body, error_regex)!r}")
    logger.info('\n'.join(reply.split('\n')[:3]))

    import datetime
    logger.error(f"REPLY: AGE IS {datetime.datetime.now(datetime.timezone.utc).timestamp() - comment.created_utc}")
    comment.reply(reply)


def main():
    reddit = praw.Reddit("scalawag_bot")
    stream = reddit.subreddit("all").stream.comments()
    to_reply_to_stream = (comment for comment in stream if should_reply(comment))
    for comment in delayed_stream(to_reply_to_stream, delay_seconds=DELAY_SECONDS):
        try:
            reply_to_comment(comment)
        except Exception as e:
            print(e)
            time.sleep(120)


if __name__ == "__main__":
    main()
