"""Exercise actual serial and worker sampler paths with a controlled text tokenizer."""

import unittest
from unittest.mock import patch

import numpy as np
from infx.bench_serving import benchmark_serving as client


class Tokenizer:
    vocab_size = 64
    name_or_path = "/controlled"

    def encode(self, text, add_special_tokens=False):
        return [ord(c) - 32 for c in text]

    def decode(self, ids):
        return "".join(chr(i + 32) for i in ids)

    def apply_chat_template(self, messages, **kwargs):
        return "{" + messages[0]["content"] + "}"


def format_fixture(path, text):
    if path != "/controlled":
        raise ValueError("Wrong model encoder path")
    return "<" + text + ">"


class Tests(unittest.TestCase):
    def test_opt_in_serial_and_worker_paths(self):
        tokenizer = Tokenizer()
        with patch.object(client, "dsv41_encode_text_chat", side_effect=format_fixture):
            np.random.seed(0)
            rows = client.sample_random_requests(
                0,
                8,
                16,
                2,
                1.0,
                tokenizer,
                use_chat_template=True,
                dsv41=True,
                num_workers=1,
            )
            self.assertEqual([x[1:3] for x in rows], [(8, 16), (8, 16)])
            self.assertTrue(
                all(r[0].startswith("<") and r[0].endswith(">") for r in rows)
            )
            with patch.object(client, "_worker_tokenizer", tokenizer, create=True):
                chunk = client._process_prompt_chunk(
                    ([0, 1], [], [6, 6], [16, 16], [0, 1], 0, 64, True, False, True, 7)
                )
            self.assertEqual([x[1:3] for x in chunk], [(8, 16), (8, 16)])
            self.assertEqual(chunk[0][0], '< !"#$%>')
        self.assertEqual(
            client._apply_chat_template("hello", tokenizer, False), "{hello}"
        )

    def test_incompatible_or_missing_chat_options(self):
        for kwargs in (
            {"dsv4": True, "dsv41": True, "use_chat_template": True},
            {"dsv41": True},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                client.sample_random_requests(
                    0, 8, 16, 2, 1.0, Tokenizer(), num_workers=1, **kwargs
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
