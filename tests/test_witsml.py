from pathlib import Path

from backend.app.services.witsml import parse_witsml_file


def test_witsml_parser_maps_units_and_preserves_provenance(tmp_path: Path):
    source = tmp_path / "sample.xml"
    source.write_text(
        """<?xml version=\"1.0\"?>
<logs xmlns=\"http://www.witsml.org/schemas/1series\">
  <log>
    <nameWell>NO 15/9-F-4</nameWell>
    <logData>
      <mnemonicList>Time,WOB,TORQUE,FLOWIN,ROP_AVG,SURF_RPM,Depth</mnemonicList>
      <unitList>unitless,N,N.m,m3/s,m/s,c/s,m</unitList>
      <data>2016-09-30T10:04:01.000Z,1000,2000,0.001,0.5,2,1234.5</data>
    </logData>
  </log>
</logs>
""",
        encoding="utf-8",
    )

    rows = parse_witsml_file(source)

    assert len(rows) == 1
    row = rows[0]
    assert row["well_name"] == "NO 15/9-F-4"
    assert row["measured_depth_m"] == 1234.5
    assert row["wob"] == 1.0
    assert row["torque"] == 2.0
    assert row["flow_rate_lpm"] == 60.0
    assert row["rop_mhr"] == 1800.0
    assert row["rpm"] == 120.0
    assert row["source_file"] == str(source)
