"""Pin numpy's and turbovec's kernels, so every machine returns the same hits.

Both libraries pick a kernel to suit the CPU, and the kernels round differently.
The differences are tiny, but neighbours in the library are often closer than
that, so on another CPU near-tied hits swap places and the output changes.

- numpy's OpenBLAS is pinned to Haswell (AVX2 and FMA), which is fast and present
  on nearly every x86-64 CPU. Where the CPU lacks it, OpenBLAS keeps its own
  choice rather than crash.
- On CPUs with AVX-512 VNNI, turbovec scores with a vector-major kernel that its
  author documents as not bit-identical to the standard one.
  ``TURBOVEC_NO_VECTOR_MAJOR`` turns it off everywhere, at a small search cost on
  those CPUs only.

Import this before anything that imports numpy or loads an index: each library
reads its setting once.
"""

import os
import platform


def _has_avx2_and_fma():
    if platform.machine() not in ("x86_64", "AMD64"):
        return False
    try:
        with open("/proc/cpuinfo") as fh:
            for line in fh:
                if line.startswith("flags"):
                    return {"avx2", "fma"} <= set(line.split(":", 1)[1].split())
    except OSError:
        pass
    return False


if _has_avx2_and_fma():
    os.environ.setdefault("OPENBLAS_CORETYPE", "Haswell")
os.environ.setdefault("TURBOVEC_NO_VECTOR_MAJOR", "1")
