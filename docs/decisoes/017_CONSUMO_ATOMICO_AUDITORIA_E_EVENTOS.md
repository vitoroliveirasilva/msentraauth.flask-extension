# ADR-017: consumo atômico, auditoria e eventos sanitizados

## Contexto

`load()` seguido de `delete()` não garante consumo único entre workers. Ao mesmo tempo, a extensão precisa expor postura e telemetria sem impor Redis ou plataforma de observabilidade.

## Decisão

- Adicionar `AtomicAuthStorage.take()` como capacidade opcional;
- Usar consumo atômico para fluxo e identidade quando disponível;
- Manter fallback local por compatibilidade, sem promessa distribuída;
- Permitir exigência por configuração;
- Expor auditoria somente leitura com achados sanitizados;
- Emitir eventos imutáveis e logging opcional com campos fechados.

## Consequências

- Backends de produção podem provar consumo único;
- `MemoryStorage` fornece atomicidade apenas no processo;
- Token cache continua last-write-wins;
- A extensão não depende de Redis nem biblioteca de logging;
- Códigos de achados e campos de evento passam a integrar a API pública experimental.
