"""Composite SVG contact-sheet export utilities."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompositeImageCell:
    """One cell in a composite SVG image grid."""

    image_path: str | Path
    row_label: str
    column_label: str


def export_composite_svg(
    cells: list[CompositeImageCell],
    output_path: str | Path,
    row_labels: list[str],
    column_labels: list[str],
    cell_width: int = 260,
    cell_height: int = 260,
    label_width: int = 160,
    header_height: int = 70,
    title: str = "Atlas Composite Overlay",
) -> Path:
    """Export a composite SVG contact sheet from existing SVG images."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    svg = composite_svg_to_string(
        cells=cells,
        row_labels=row_labels,
        column_labels=column_labels,
        cell_width=cell_width,
        cell_height=cell_height,
        label_width=label_width,
        header_height=header_height,
        title=title,
        output_path=path,
    )

    path.write_text(svg, encoding="utf-8")

    return path


def composite_svg_to_string(
    cells: list[CompositeImageCell],
    row_labels: list[str],
    column_labels: list[str],
    cell_width: int,
    cell_height: int,
    label_width: int,
    header_height: int,
    title: str,
    output_path: Path,
) -> str:
    """Build composite SVG text."""
    rows = len(row_labels)
    cols = len(column_labels)

    width = label_width + cols * cell_width
    height = header_height + rows * cell_height

    cell_lookup = {
        (cell.row_label, cell.column_label): cell
        for cell in cells
    }

    lines = [
        _svg_header(width, height),
        '<rect x="0" y="0" width="100%" height="100%" fill="white" />',
        f'<text x="{width / 2:.2f}" y="32" text-anchor="middle" '
        f'font-size="24" font-family="Arial" font-weight="bold">{title}</text>',
    ]

    for col_index, column_label in enumerate(column_labels):
        x = label_width + col_index * cell_width + cell_width / 2
        lines.append(
            f'<text x="{x:.2f}" y="60" text-anchor="middle" '
            f'font-size="16" font-family="Arial" font-weight="bold">'
            f'{column_label.title()}</text>'
        )

    for row_index, row_label in enumerate(row_labels):
        y = header_height + row_index * cell_height

        lines.append(
            f'<text x="{label_width / 2:.2f}" y="{y + cell_height / 2:.2f}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-size="15" font-family="Arial" font-weight="bold">'
            f'{_label_title(row_label)}</text>'
        )

        for col_index, column_label in enumerate(column_labels):
            x = label_width + col_index * cell_width
            cell = cell_lookup.get((row_label, column_label))

            lines.append(
                f'<rect x="{x}" y="{y}" width="{cell_width}" '
                f'height="{cell_height}" fill="none" stroke="#999" '
                f'stroke-width="1" />'
            )

            if cell is None:
                continue

            relative_path = _relative_href(output_path, Path(cell.image_path))

            lines.append(
                f'<image href="{relative_path}" '
                f'x="{x + 10}" y="{y + 10}" '
                f'width="{cell_width - 20}" height="{cell_height - 20}" '
                f'preserveAspectRatio="xMidYMid meet" />'
            )

    lines.append("</svg>")

    return "\n".join(lines)


def _svg_header(width: int, height: int) -> str:
    """Return SVG header."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )


def _relative_href(output_path: Path, image_path: Path) -> str:
    """Return image path relative to composite output location."""
    try:
        return image_path.relative_to(output_path.parent).as_posix()
    except ValueError:
        return image_path.as_posix()


def _label_title(label: str) -> str:
    """Format row labels."""
    return label.replace("_", " ").title()