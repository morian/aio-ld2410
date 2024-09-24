import pytest

from aio_ld2410.protocol import Report, ReportFrame, ReportType

_TRACES = {
    ReportType.BASIC: 'f4 f3 f2 f1 0d 00 02 aa 02 51 00 00 00 00 3b 00 00 55 00 f8 f7 f6 f5',
    ReportType.ENGINEERING: (
        'f4 f3 f2 f1 23 00 01 aa 03 1e 00 3c 00 00 39 00'
        '00 08 08 3c 22 05 03 03 04 03 06 05 00 00 39 10'
        '13 06 06 08 04 60 01 55 00 f8 f7 f6 f5'
    ),
}


@pytest.mark.parametrize(('type_', 'trace'), _TRACES.items())
def test_good_reports(type_, trace):
    frame = ReportFrame.parse(bytes.fromhex(trace))
    report = Report.parse(frame.data)
    print(report)
