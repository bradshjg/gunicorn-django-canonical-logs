from __future__ import annotations

import os
import pathlib
import sys
import sysconfig
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import traceback


def _filter_stack_summary(
    stack_summary: traceback.StackSummary,
) -> tuple[list[traceback.FrameSummary], list[traceback.FrameSummary]]:
    library_paths = sysconfig.get_paths().values()
    library_frames, app_frames = [], []
    for frame_summary in stack_summary:
        if any(frame_summary.filename.startswith((path, os.path.realpath(path))) for path in library_paths):
            library_frames.append(frame_summary)
        else:
            app_frames.append(frame_summary)
    return library_frames, app_frames


def _format_frame_summary(frame_summary: traceback.FrameSummary | None) -> str | None:
    if not frame_summary:
        return
    # use sys.path to find the shortest possible import (i.e. strip base project path)
    python_paths = sorted(sys.path, key=len, reverse=True)
    fname = frame_summary.filename
    for path in python_paths:
        if fname.startswith(path):
            to_remove = path if path.endswith("/") else path + "/"
            fname = fname.removeprefix(to_remove)
            break

    return f"{fname}:{frame_summary.lineno}:{frame_summary.name}"


def get_stack_loc_context(stack_summary: traceback.StackSummary):
    library_frames, app_frames = _filter_stack_summary(stack_summary)

    if not app_frames:
        loc, cause_loc = library_frames[0], library_frames[-1]
    elif len(app_frames) > 1:
        loc, cause_loc = app_frames[0], app_frames[-1]
    else:
        loc, cause_loc = app_frames[0], stack_summary[-1]
    return {
        "loc": _format_frame_summary(loc),
        "cause_loc": _format_frame_summary(cause_loc),
    }
