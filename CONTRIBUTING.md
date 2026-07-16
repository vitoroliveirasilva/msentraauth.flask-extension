# Contribuindo

## Ambiente pretendido

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

No PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

O comando será validado após criação do `pyproject.toml`.

## Branches

- `dev`: desenvolvimento;
- `prod`: estado estável.

## Padrões

- Python tipado;
- Application factory;
- Nenhuma credencial em testes;
- Testes de sucesso e falha;
- API pública documentada;
- Comentários explicam motivo;
- Nomes públicos em inglês e documentação em português.