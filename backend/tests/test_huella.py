"""Huella de contenido: sirve para saber si una evaluacion corresponde al codigo actual sin depender de fechas de archivo."""
from src.comun import huella as H


def test_la_huella_ignora_los_saltos_de_linea_y_detecta_cualquier_cambio(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "RAIZ", str(tmp_path))
    (tmp_path / "a.txt").write_bytes(b"uno\r\ndos\r\n")   # como queda un archivo en Windows
    h = H.huella(["a.txt"])
    (tmp_path / "a.txt").write_bytes(b"uno\ndos\n")        # como queda en Linux
    assert H.huella(["a.txt"]) == h
    (tmp_path / "a.txt").write_bytes(b"uno\ndos!\n")
    assert H.huella(["a.txt"]) != h


def test_la_huella_depende_de_que_archivos_hay_y_no_del_orden_en_que_se_listan(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "RAIZ", str(tmp_path))
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.py").write_text("y = 2\n")
    assert H.huella(["a.py", "b.py"]) == H.huella(["*.py"]) == H.huella(["b.py", "a.py"])
    assert H.huella(["a.py"]) != H.huella(["a.py", "b.py"])


def test_un_archivo_renombrado_cambia_la_huella_aunque_su_contenido_sea_igual(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "RAIZ", str(tmp_path))
    (tmp_path / "a.py").write_text("x = 1\n")
    antes = H.huella(["*.py"])
    (tmp_path / "a.py").rename(tmp_path / "b.py")
    assert H.huella(["*.py"]) != antes
