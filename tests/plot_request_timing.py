import argparse
import os


WIDTH = 960
HEIGHT = 480
MARGIN_LEFT = 70
MARGIN_RIGHT = 30
MARGIN_TOP = 40
MARGIN_BOTTOM = 60


def read_timing_log(path):
    process_values = []
    total_values = []

    with open(path, 'r') as file:
        header = file.readline().strip().split(';')
        try:
            process_index = header.index('process_ms')
            total_index = header.index('total_ms')
        except ValueError:
            raise ValueError('Expected header: process_ms;total_ms')

        for line in file:
            line = line.strip()
            if not line:
                continue
            parts = line.split(';')
            try:
                process_values.append(float(parts[process_index]))
                total_values.append(float(parts[total_index]))
            except (IndexError, ValueError):
                continue

    return process_values, total_values


def make_line_chart(process_values, total_values, output_path):
    count = len(process_values)
    max_value = max(process_values + total_values + [1])
    plot_width = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_height = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

    def x_at(index):
        if count <= 1:
            return MARGIN_LEFT + plot_width / 2
        return MARGIN_LEFT + index * plot_width / (count - 1)

    def y_at(value):
        return MARGIN_TOP + plot_height - value * plot_height / max_value

    process_points = ' '.join(
        '{0:.2f},{1:.2f}'.format(x_at(index), y_at(value))
        for index, value in enumerate(process_values)
    )
    total_points = ' '.join(
        '{0:.2f},{1:.2f}'.format(x_at(index), y_at(value))
        for index, value in enumerate(total_values)
    )

    body = [
        _svg_header('Request Processing Time by Request'),
        _axes(max_value, count),
        '<polyline points="{0}" fill="none" stroke="#2563eb" stroke-width="2" />'.format(process_points),
        '<polyline points="{0}" fill="none" stroke="#dc2626" stroke-width="2" />'.format(total_points),
        _legend([('process_ms', '#2563eb'), ('total_ms', '#dc2626')]),
        _svg_footer(),
    ]
    _write_svg(output_path, body)


def make_average_bar_chart(process_values, total_values, output_path):
    process_avg = sum(process_values) / len(process_values)
    total_avg = sum(total_values) / len(total_values)
    max_value = max(process_avg, total_avg, 1)
    plot_height = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    baseline = HEIGHT - MARGIN_BOTTOM
    bar_width = 140
    gap = 110
    start_x = MARGIN_LEFT + 230

    process_height = process_avg * plot_height / max_value
    total_height = total_avg * plot_height / max_value

    body = [
        _svg_header('Average Request Time'),
        _axes(max_value, 2),
        _bar(start_x, baseline, bar_width, process_height, '#2563eb', 'process_ms', process_avg),
        _bar(start_x + bar_width + gap, baseline, bar_width, total_height, '#dc2626', 'total_ms', total_avg),
        _svg_footer(),
    ]
    _write_svg(output_path, body)


def _svg_header(title):
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" viewBox="0 0 {0} {1}">
<rect width="100%" height="100%" fill="#ffffff" />
<text x="{2}" y="26" font-family="Arial, sans-serif" font-size="20" font-weight="700">{3}</text>'''.format(
        WIDTH, HEIGHT, MARGIN_LEFT, title
    )


def _svg_footer():
    return '</svg>'


def _axes(max_value, count):
    plot_width = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_height = HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    baseline = HEIGHT - MARGIN_BOTTOM
    right = WIDTH - MARGIN_RIGHT
    parts = [
        '<line x1="{0}" y1="{1}" x2="{2}" y2="{1}" stroke="#111827" stroke-width="1" />'.format(
            MARGIN_LEFT, baseline, right
        ),
        '<line x1="{0}" y1="{1}" x2="{0}" y2="{2}" stroke="#111827" stroke-width="1" />'.format(
            MARGIN_LEFT, MARGIN_TOP, baseline
        ),
    ]

    for tick in range(5):
        value = max_value * tick / 4
        y = baseline - plot_height * tick / 4
        parts.append('<line x1="{0}" y1="{1:.2f}" x2="{2}" y2="{1:.2f}" stroke="#e5e7eb" />'.format(
            MARGIN_LEFT, y, right
        ))
        parts.append('<text x="12" y="{0:.2f}" font-family="Arial, sans-serif" font-size="12">{1:.2f} ms</text>'.format(
            y + 4, value
        ))

    parts.append('<text x="{0}" y="{1}" font-family="Arial, sans-serif" font-size="12">request index, n={2}</text>'.format(
        MARGIN_LEFT + plot_width / 2 - 50, HEIGHT - 18, count
    ))
    return '\n'.join(parts)


def _legend(items):
    parts = []
    x = WIDTH - 220
    y = 24
    for index, item in enumerate(items):
        label, color = item
        item_y = y + index * 22
        parts.append('<rect x="{0}" y="{1}" width="14" height="14" fill="{2}" />'.format(x, item_y - 11, color))
        parts.append('<text x="{0}" y="{1}" font-family="Arial, sans-serif" font-size="13">{2}</text>'.format(
            x + 22, item_y, label
        ))
    return '\n'.join(parts)


def _bar(x, baseline, width, height, color, label, value):
    y = baseline - height
    return '''<rect x="{0}" y="{1:.2f}" width="{2}" height="{3:.2f}" fill="{4}" />
<text x="{5}" y="{6}" font-family="Arial, sans-serif" font-size="14" text-anchor="middle">{7}</text>
<text x="{5}" y="{8:.2f}" font-family="Arial, sans-serif" font-size="13" text-anchor="middle">{9:.2f} ms</text>'''.format(
        x, y, width, height, color, x + width / 2, baseline + 24, label, y - 8, value
    )


def _write_svg(path, parts):
    with open(path, 'w') as file:
        file.write('\n'.join(parts))


def main():
    parser = argparse.ArgumentParser(description='Build SVG charts from resources/request_timing.log')
    parser.add_argument('--input', default=os.path.join('resources', 'request_timing.log'))
    parser.add_argument('--output-dir', default=os.path.join('tests', 'request_timing_charts'))
    args = parser.parse_args()

    process_values, total_values = read_timing_log(args.input)
    if not process_values:
        raise SystemExit('No timing rows found in {0}'.format(args.input))

    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)

    line_chart = os.path.join(args.output_dir, 'request_timing_by_request.svg')
    average_chart = os.path.join(args.output_dir, 'request_timing_average.svg')
    make_line_chart(process_values, total_values, line_chart)
    make_average_bar_chart(process_values, total_values, average_chart)

    print('Created:')
    print(line_chart)
    print(average_chart)


if __name__ == '__main__':
    main()
