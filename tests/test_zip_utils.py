import io
import zlib

import pytest

from sc4_mapper.zipUtils import ZipInputStream


def test_zip_input_stream_read():
    content = b"Hello World\nThis is a test\nWith multiple lines"
    compressed_content = zlib.compress(content)

    stream = ZipInputStream(io.BytesIO(compressed_content))

    # Test read(bytes)
    assert stream.read(5) == b"Hello"
    assert stream.read(6) == b" World"

    # Test read() until end
    assert stream.read() == b"\nThis is a test\nWith multiple lines"
    assert stream.read() == b""


def test_zip_input_stream_readline():
    content = b"Line 1\nLine 2\nLine 3"
    compressed_content = zlib.compress(content)

    stream = ZipInputStream(io.BytesIO(compressed_content))

    assert stream.readline() == b"Line 1\n"
    assert stream.readline() == b"Line 2\n"
    assert stream.readline() == b"Line 3"
    assert stream.readline() == b""


def test_zip_input_stream_readlines():
    content = b"Line 1\nLine 2\nLine 3"
    compressed_content = zlib.compress(content)

    stream = ZipInputStream(io.BytesIO(compressed_content))

    assert stream.readlines() == [b"Line 1\n", b"Line 2\n", b"Line 3"]


def test_zip_input_stream_seek_tell():
    content = b"0123456789ABCDEF"
    compressed_content = zlib.compress(content)

    stream = ZipInputStream(io.BytesIO(compressed_content))

    assert stream.tell() == 0
    assert stream.read(4) == b"0123"
    assert stream.tell() == 4

    stream.seek(2, 1)  # seek from current pos
    assert stream.tell() == 6
    assert stream.read(2) == b"67"

    stream.seek(10, 0)  # seek from start
    assert stream.tell() == 10
    assert stream.read(2) == b"AB"


def test_zip_input_stream_seek_errors():
    content = b"0123456789"
    compressed_content = zlib.compress(content)
    stream = ZipInputStream(io.BytesIO(compressed_content))

    stream.read(5)

    with pytest.raises(IOError, match="Cannot seek backwards"):
        stream.seek(2, 0)

    with pytest.raises(IOError, match="Illegal argument"):
        stream.seek(0, 3)


def test_zip_input_stream_large_data():
    content = b"A" * (1024 * 1024 * 2)  # 2MB
    compressed_content = zlib.compress(content)

    stream = ZipInputStream(io.BytesIO(compressed_content))

    chunk1 = stream.read(1024 * 512)
    assert chunk1 == b"A" * (1024 * 512)
    assert stream.tell() == 1024 * 512

    remaining = stream.read()
    assert len(remaining) == (1024 * 1024 * 2) - (1024 * 512)
    assert remaining == b"A" * len(remaining)
