"""
Chương trình dòng lệnh nén / giải nén file văn bản bằng thuật toán Huffman.

Cách dùng:
    python main.py compress   <file_goc.txt> <file_nen.huf>
    python main.py decompress <file_nen.huf> <file_khoi_phuc.txt>
    python main.py demo       <file_goc.txt>

Chế độ "demo" chạy đủ các bước: nén -> giải nén -> so sánh dung lượng
-> kiểm tra file khôi phục có giống hệt file gốc hay không.
"""

import os
import sys
import time

from huffman import compress_file, decompress_file


def show_code_table(freq, codes, limit=10):
    """In các ký tự xuất hiện nhiều nhất cùng mã Huffman của chúng."""
    print(f"\nBảng mã Huffman ({limit} ký tự xuất hiện nhiều nhất):")
    print(f"  {'Ký tự':<8}{'Tần suất':>10}  Mã")
    top = sorted(freq, key=lambda ch: freq[ch], reverse=True)[:limit]
    for ch in top:
        print(f"  {repr(ch):<8}{freq[ch]:>10}  {codes[ch]}")


def show_sizes(original_path, compressed_path, header_size):
    """So sánh dung lượng trước và sau khi nén (tính bằng byte)."""
    original = os.path.getsize(original_path)
    compressed = os.path.getsize(compressed_path)
    print(f"\nDung lượng file gốc : {original:>10,} byte")
    print(f"Dung lượng file nén : {compressed:>10,} byte"
          f"  (header {header_size:,} + dữ liệu {compressed - header_size:,})")
    if original > 0 and compressed > 0:
        # Compression Ratio = gốc / nén (lớn hơn 1 nghĩa là file đã nhỏ đi)
        # Space Saving = (1 - nén / gốc) x 100%
        ratio = original / compressed
        saving = (1 - compressed / original) * 100
        print(f"Compression Ratio   : {ratio:>10.2f}  (file gốc / file nén)")
        print(f"Space Saving        : {saving:>9.2f} %")


def compress(input_path, output_path):
    start = time.perf_counter()
    text, freq, codes, num_bits, header_size = compress_file(input_path,
                                                             output_path)
    elapsed = time.perf_counter() - start
    print(f"Đã nén '{input_path}' -> '{output_path}' ({elapsed:.3f} giây)")
    print(f"Số ký tự n = {len(text):,}, số ký tự khác nhau k = {len(freq)}")
    if text:
        print(f"Độ dài mã trung bình: {num_bits / len(text):.3f} bit/ký tự")
    show_code_table(freq, codes)
    show_sizes(input_path, output_path, header_size)


def decompress(input_path, output_path):
    start = time.perf_counter()
    text = decompress_file(input_path, output_path)
    elapsed = time.perf_counter() - start
    print(f"Đã giải nén '{input_path}' -> '{output_path}' "
          f"({len(text):,} ký tự, {elapsed:.3f} giây)")


def demo(input_path):
    base = os.path.splitext(input_path)[0]
    compressed_path = base + ".huf"
    restored_path = base + "_restored.txt"

    print("=== 1. NÉN ===")
    compress(input_path, compressed_path)

    print("\n=== 2. GIẢI NÉN ===")
    decompress(compressed_path, restored_path)

    # Bước 7: so sánh từng byte giữa file gốc và file sau giải nén.
    print("\n=== 3. KIỂM TRA ===")
    with open(input_path, "rb") as f1, open(restored_path, "rb") as f2:
        same = f1.read() == f2.read()
    print("Khôi phục chính xác:", "CÓ" if same else "KHÔNG")


def main():
    # In tiếng Việt ra màn hình console (đặc biệt trên Windows).
    sys.stdout.reconfigure(encoding="utf-8")

    args = sys.argv[1:]
    if len(args) == 3 and args[0] == "compress":
        compress(args[1], args[2])
    elif len(args) == 3 and args[0] == "decompress":
        decompress(args[1], args[2])
    elif len(args) == 2 and args[0] == "demo":
        demo(args[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
