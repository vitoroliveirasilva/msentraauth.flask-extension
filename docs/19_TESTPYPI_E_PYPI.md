# TestPyPI, PyPI e Trusted Publishing

O workflow `.github/workflows/release.yml` separa construção e publicação. O job de build produz uma única dupla imutável de wheel e source distribution, executa toda a qualidade e envia os arquivos como artifact interno.

## TestPyPI

A execução manual de `Release` publica no environment `testpypi`. Ela existe para validar metadata, instalação e compatibilidade do consumidor sem criar uma versão pública definitiva.

Exemplo de instalação após a publicação de teste:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  flask-ms-entra-auth==1.0.0
```

O índice adicional é necessário porque dependências normais podem não existir no TestPyPI.

## PyPI

A publicação de produção ocorre somente quando uma GitHub Release é publicada. A tag deve ser exatamente `v<versão>`, por exemplo `v1.0.0`. O script `scripts/verify_release.py` impede versão instável, tag divergente e distribuição incompatível.

## Credenciais

A automação usa OIDC por `id-token: write` e `pypa/gh-action-pypi-publish`. Não existe API token no repositório. Os projetos correspondentes precisam ser configurados previamente como Trusted Publishers no TestPyPI e no PyPI.
