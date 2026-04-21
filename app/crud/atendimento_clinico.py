from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.atendimento_clinico import AtendimentoClinico
from app.models.atendimento_clinico_item import AtendimentoClinicoItem
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.funcionario import Funcionario
from app.models.pet import Pet
from app.models.pet_anamnese import PetAnamnese
from app.models.pet_prontuario import PetProntuario
from app.models.servico import Servico
from app.schemas.atendimento_clinico import (
    AtendimentoClinicoAnamneseSalvar,
    AtendimentoClinicoIniciar,
    AtendimentoClinicoItemCreate,
    AtendimentoClinicoProntuarioSalvar,
)


def _touch_updated_at(atendimento: AtendimentoClinico):
    if hasattr(atendimento, "updated_at"):
        atendimento.updated_at = datetime.utcnow()


def _valor_texto_limpo(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def _resolver_logo_empresa(empresa):
    if not empresa:
        return None

    for campo in ("logo_url", "logo", "logotipo", "url_logo", "imagem_logo"):
        if hasattr(empresa, campo):
            valor = _valor_texto_limpo(getattr(empresa, campo, None))
            if valor:
                return valor

    return None


def _resolver_endereco_empresa_receita(empresa):
    if not empresa:
        return ""

    endereco_loja = _valor_texto_limpo(getattr(empresa, "endereco_loja", None))
    if endereco_loja:
        return endereco_loja

    logradouro = _valor_texto_limpo(getattr(empresa, "logradouro", None))
    numero = _valor_texto_limpo(getattr(empresa, "numero", None))
    complemento = _valor_texto_limpo(getattr(empresa, "complemento", None))
    bairro = _valor_texto_limpo(getattr(empresa, "bairro", None))
    cidade = _valor_texto_limpo(getattr(empresa, "cidade", None))
    uf = _valor_texto_limpo(getattr(empresa, "uf", None))
    cep = _valor_texto_limpo(getattr(empresa, "cep", None))

    linha1 = ", ".join([parte for parte in [logradouro, numero] if parte])
    linha2 = " - ".join([parte for parte in [complemento, bairro] if parte])
    linha3 = " / ".join([parte for parte in [cidade, uf] if parte])

    partes = [parte for parte in [linha1, linha2, linha3, cep] if parte]
    return "\n".join(partes).strip()


def _montar_texto_exame(exame):
    nome = _valor_texto_limpo(getattr(exame, "nome", None))
    tipo = _valor_texto_limpo(getattr(exame, "tipo", None))
    descricao = _valor_texto_limpo(getattr(exame, "descricao", None))
    resultado = _valor_texto_limpo(getattr(exame, "resultado", None))
    observacoes = _valor_texto_limpo(getattr(exame, "observacoes", None))

    partes = []

    if nome and tipo:
        partes.append(f"{nome} ({tipo})")
    elif nome:
        partes.append(nome)
    elif tipo:
        partes.append(tipo)

    if descricao:
        partes.append(descricao)

    if resultado:
        partes.append(f"Resultado: {resultado}")

    if observacoes:
        partes.append(f"Observações: {observacoes}")

    return " - ".join([parte for parte in partes if parte])


def _extrair_bloco_observacao(texto: str, chave: str) -> str:
    bruto = str(texto or "")
    marcador = f"[{chave}]"

    if marcador not in bruto:
        return ""

    inicio = bruto.find(marcador)
    if inicio < 0:
        return ""

    inicio += len(marcador)

    resto = bruto[inicio:]
    proximos_marcadores = ["[OBSERVACOES_GERAIS]", "[MEDICACOES]", "[EXAMES]", "[RECEITA]"]

    fim = len(resto)
    for proximo in proximos_marcadores:
        pos = resto.find(proximo)
        if pos > 0:
            fim = min(fim, pos)

    return resto[:fim].strip()


def _extrair_observacoes_clinicas_serializadas(texto: str) -> dict:
    bruto = str(texto or "")

    if "[OBSERVACOES_GERAIS]" not in bruto:
        return {
            "observacoes_gerais": bruto.strip(),
            "medicacoes": "",
            "exames": "",
            "receita": "",
        }

    return {
        "observacoes_gerais": _extrair_bloco_observacao(bruto, "OBSERVACOES_GERAIS"),
        "medicacoes": _extrair_bloco_observacao(bruto, "MEDICACOES"),
        "exames": _extrair_bloco_observacao(bruto, "EXAMES"),
        "receita": _extrair_bloco_observacao(bruto, "RECEITA"),
    }


def _get_atendimento_or_404(db: Session, atendimento_id: int) -> AtendimentoClinico:
    atendimento = (
        db.query(AtendimentoClinico)
        .options(
            joinedload(AtendimentoClinico.empresa),
            joinedload(AtendimentoClinico.anamnese),
            joinedload(AtendimentoClinico.prontuario),
            joinedload(AtendimentoClinico.itens),
            joinedload(AtendimentoClinico.pet),
            joinedload(AtendimentoClinico.cliente),
            joinedload(AtendimentoClinico.veterinario),
            joinedload(AtendimentoClinico.agendamento),
            joinedload(AtendimentoClinico.exames),
            joinedload(AtendimentoClinico.receitas),
        )
        .filter(AtendimentoClinico.id == atendimento_id)
        .first()
    )

    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento clínico não encontrado.")

    return atendimento


def _finalizar_agendamento_vinculado_se_existir(atendimento: AtendimentoClinico):
    agendamento = getattr(atendimento, "agendamento", None)

    if not agendamento:
        return

    if hasattr(agendamento, "status"):
        agendamento.status = "FINALIZADO"


def iniciar_atendimento(db: Session, payload: AtendimentoClinicoIniciar) -> AtendimentoClinico:
    empresa = db.query(Empresa).filter(Empresa.id == payload.empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    pet = db.query(Pet).filter(Pet.id == payload.pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado.")

    cliente = db.query(Cliente).filter(Cliente.id == payload.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    if hasattr(pet, "cliente_id") and getattr(pet, "cliente_id", None) != payload.cliente_id:
        raise HTTPException(
            status_code=400,
            detail="O pet informado não pertence ao cliente selecionado.",
        )

    if payload.veterinario_id:
        veterinario = db.query(Funcionario).filter(Funcionario.id == payload.veterinario_id).first()
        if not veterinario:
            raise HTTPException(status_code=404, detail="Veterinário/funcionário não encontrado.")

    if payload.agendamento_id:
        agendamento = db.query(Agendamento).filter(Agendamento.id == payload.agendamento_id).first()
        if not agendamento:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

        if hasattr(agendamento, "pet_id") and getattr(agendamento, "pet_id", None) != payload.pet_id:
            raise HTTPException(
                status_code=400,
                detail="O agendamento não pertence ao pet informado.",
            )

    atendimento_existente = None
    if payload.agendamento_id:
        atendimento_existente = (
            db.query(AtendimentoClinico)
            .filter(
                AtendimentoClinico.agendamento_id == payload.agendamento_id,
                AtendimentoClinico.status.in_(["EM_ATENDIMENTO", "ABERTO"]),
            )
            .first()
        )

    if atendimento_existente:
        return _get_atendimento_or_404(db, atendimento_existente.id)

    atendimento = AtendimentoClinico(
        empresa_id=payload.empresa_id,
        agendamento_id=payload.agendamento_id,
        pet_id=payload.pet_id,
        cliente_id=payload.cliente_id,
        veterinario_id=payload.veterinario_id,
        status="EM_ATENDIMENTO",
        data_inicio=datetime.utcnow(),
        observacoes_recepcao=payload.observacoes_recepcao,
        enviado_pdv=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(atendimento)
    db.flush()

    anamnese = PetAnamnese()
    if hasattr(anamnese, "atendimento_id"):
        anamnese.atendimento_id = atendimento.id
    if hasattr(anamnese, "pet_id"):
        anamnese.pet_id = atendimento.pet_id
    if hasattr(anamnese, "created_at"):
        anamnese.created_at = datetime.utcnow()
    if hasattr(anamnese, "updated_at"):
        anamnese.updated_at = datetime.utcnow()
    db.add(anamnese)

    prontuario = PetProntuario()
    if hasattr(prontuario, "atendimento_id"):
        prontuario.atendimento_id = atendimento.id
    if hasattr(prontuario, "pet_id"):
        prontuario.pet_id = atendimento.pet_id
    if hasattr(prontuario, "created_at"):
        prontuario.created_at = datetime.utcnow()
    if hasattr(prontuario, "updated_at"):
        prontuario.updated_at = datetime.utcnow()
    db.add(prontuario)

    db.commit()
    db.refresh(atendimento)

    return _get_atendimento_or_404(db, atendimento.id)


def iniciar_por_agendamento(db: Session, agendamento_id: int, empresa_id: int) -> AtendimentoClinico:
    agendamento = (
        db.query(Agendamento)
        .options(
            joinedload(Agendamento.servicos_agendamento).joinedload(AgendamentoServico.servico)
        )
        .filter(Agendamento.id == agendamento_id)
        .first()
    )

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    if hasattr(agendamento, "empresa_id") and getattr(agendamento, "empresa_id", None) != empresa_id:
        raise HTTPException(
            status_code=400,
            detail="O agendamento não pertence à empresa informada.",
        )

    possui_servico_veterinario = False
    for rel in getattr(agendamento, "servicos_agendamento", []) or []:
        servico = getattr(rel, "servico", None)
        if servico and getattr(servico, "tipo_servico", None) == "VETERINARIO":
            possui_servico_veterinario = True
            break

    if not possui_servico_veterinario:
        raise HTTPException(
            status_code=400,
            detail="O agendamento informado não pertence à agenda veterinária.",
        )

    payload = AtendimentoClinicoIniciar(
        empresa_id=empresa_id,
        agendamento_id=agendamento.id,
        pet_id=getattr(agendamento, "pet_id", None),
        cliente_id=getattr(agendamento, "cliente_id", None),
        veterinario_id=getattr(agendamento, "funcionario_id", None),
        observacoes_recepcao=getattr(agendamento, "observacoes", None),
    )

    return iniciar_atendimento(db, payload)


def obter_atendimento(db: Session, atendimento_id: int) -> AtendimentoClinico:
    return _get_atendimento_or_404(db, atendimento_id)


def salvar_anamnese(
    db: Session,
    atendimento_id: int,
    payload: AtendimentoClinicoAnamneseSalvar,
) -> PetAnamnese:
    atendimento = _get_atendimento_or_404(db, atendimento_id)

    anamnese = atendimento.anamnese
    if not anamnese:
        anamnese = PetAnamnese()

        if hasattr(anamnese, "atendimento_id"):
            anamnese.atendimento_id = atendimento.id
        if hasattr(anamnese, "pet_id"):
            anamnese.pet_id = atendimento.pet_id
        if hasattr(anamnese, "created_at"):
            anamnese.created_at = datetime.utcnow()

        db.add(anamnese)
        db.flush()

    campos = {
        "queixa_principal": payload.queixa_principal,
        "historico_atual": payload.historico_atual,
        "alimentacao": payload.alimentacao,
        "alergias": payload.alergias,
        "uso_medicacao_atual": payload.uso_medicacao_atual,
        "observacoes": payload.observacoes,
    }

    for campo, valor in campos.items():
        if hasattr(anamnese, campo):
            setattr(anamnese, campo, valor)

    if hasattr(anamnese, "updated_at"):
        anamnese.updated_at = datetime.utcnow()

    _touch_updated_at(atendimento)

    db.commit()
    db.refresh(anamnese)

    return anamnese


def salvar_prontuario(
    db: Session,
    atendimento_id: int,
    payload: AtendimentoClinicoProntuarioSalvar,
) -> PetProntuario:
    atendimento = _get_atendimento_or_404(db, atendimento_id)

    prontuario = atendimento.prontuario
    if not prontuario:
        prontuario = PetProntuario()

        if hasattr(prontuario, "atendimento_id"):
            prontuario.atendimento_id = atendimento.id
        if hasattr(prontuario, "pet_id"):
            prontuario.pet_id = atendimento.pet_id
        if hasattr(prontuario, "created_at"):
            prontuario.created_at = datetime.utcnow()

        db.add(prontuario)
        db.flush()

    campos = {
        "exame_fisico": payload.exame_fisico,
        "diagnostico": payload.diagnostico,
        "conduta": payload.conduta,
        "observacoes": payload.observacoes,
    }

    for campo, valor in campos.items():
        if hasattr(prontuario, campo):
            setattr(prontuario, campo, valor)

    if hasattr(prontuario, "updated_at"):
        prontuario.updated_at = datetime.utcnow()

    if hasattr(atendimento, "observacoes_clinicas"):
        atendimento.observacoes_clinicas = payload.observacoes

    if hasattr(atendimento, "status"):
        atendimento.status = "FINALIZADO"

    if hasattr(atendimento, "data_fim"):
        atendimento.data_fim = datetime.utcnow()

    _finalizar_agendamento_vinculado_se_existir(atendimento)
    _touch_updated_at(atendimento)

    db.commit()
    db.refresh(prontuario)

    return prontuario


def adicionar_item(
    db: Session,
    atendimento_id: int,
    payload: AtendimentoClinicoItemCreate,
) -> AtendimentoClinicoItem:
    atendimento = _get_atendimento_or_404(db, atendimento_id)

    if atendimento.status == "FINALIZADO":
        raise HTTPException(
            status_code=400,
            detail="Não é possível incluir itens em atendimento finalizado.",
        )

    if payload.servico_id:
        servico = db.query(Servico).filter(Servico.id == payload.servico_id).first()
        if not servico:
            raise HTTPException(status_code=404, detail="Serviço não encontrado.")

    item = AtendimentoClinicoItem(
        atendimento_id=atendimento.id,
        servico_id=payload.servico_id,
        descricao=payload.descricao,
        quantidade=payload.quantidade,
        valor_unitario=payload.valor_unitario,
        tipo_item=payload.tipo_item,
        created_at=datetime.utcnow(),
    )

    if hasattr(item, "calcular_total") and callable(item.calcular_total):
        item.calcular_total()
    else:
        item.valor_total = (payload.quantidade or 0) * (payload.valor_unitario or 0)

    db.add(item)

    _touch_updated_at(atendimento)

    db.commit()
    db.refresh(item)

    return item


def listar_itens(db: Session, atendimento_id: int):
    _get_atendimento_or_404(db, atendimento_id)

    return (
        db.query(AtendimentoClinicoItem)
        .filter(AtendimentoClinicoItem.atendimento_id == atendimento_id)
        .order_by(AtendimentoClinicoItem.id.asc())
        .all()
    )


def calcular_total_faturavel(db: Session, atendimento_id: int) -> float:
    itens = listar_itens(db, atendimento_id)
    total = 0.0

    for item in itens:
        total += float(getattr(item, "valor_total", 0) or 0)

    return total


def gerar_payload_pdv(db: Session, atendimento_id: int) -> dict:
    atendimento = _get_atendimento_or_404(db, atendimento_id)
    itens = listar_itens(db, atendimento_id)

    itens_payload = []
    total = 0.0

    for item in itens:
        valor_total = float(getattr(item, "valor_total", 0) or 0)
        total += valor_total

        itens_payload.append(
            {
                "origem": "ATENDIMENTO_CLINICO",
                "atendimento_id": atendimento.id,
                "item_id": item.id,
                "servico_id": item.servico_id,
                "descricao": item.descricao,
                "tipo_item": item.tipo_item,
                "quantidade": item.quantidade,
                "valor_unitario": float(item.valor_unitario or 0),
                "valor_total": valor_total,
                "pet_id": atendimento.pet_id,
                "cliente_id": atendimento.cliente_id,
                "empresa_id": atendimento.empresa_id,
                "data_referencia": (
                    atendimento.data_fim.isoformat()
                    if atendimento.data_fim
                    else atendimento.data_inicio.isoformat()
                    if atendimento.data_inicio
                    else None
                ),
            }
        )

    return {
        "origem": "CLINICO",
        "empresa_id": atendimento.empresa_id,
        "cliente_id": atendimento.cliente_id,
        "pet_id": atendimento.pet_id,
        "atendimento_id": atendimento.id,
        "agendamento_id": atendimento.agendamento_id,
        "data_atendimento": (
            atendimento.data_fim.isoformat()
            if atendimento.data_fim
            else atendimento.data_inicio.isoformat()
            if atendimento.data_inicio
            else None
        ),
        "itens": itens_payload,
        "total_faturavel": total,
        "consolidar_mesmo_dia": True,
        "observacao": "Payload preparado para integração posterior com PDV consolidado.",
    }


def finalizar_atendimento(db: Session, atendimento_id: int) -> AtendimentoClinico:
    atendimento = _get_atendimento_or_404(db, atendimento_id)

    if atendimento.status == "FINALIZADO":
        return atendimento

    if hasattr(atendimento, "finalizar") and callable(atendimento.finalizar):
        atendimento.finalizar()
    else:
        atendimento.status = "FINALIZADO"
        atendimento.data_fim = datetime.utcnow()

    _finalizar_agendamento_vinculado_se_existir(atendimento)
    _touch_updated_at(atendimento)

    db.commit()

    return _get_atendimento_or_404(db, atendimento_id)


def marcar_enviado_pdv(db: Session, atendimento_id: int) -> AtendimentoClinico:
    atendimento = _get_atendimento_or_404(db, atendimento_id)

    if hasattr(atendimento, "marcar_enviado_pdv") and callable(atendimento.marcar_enviado_pdv):
        atendimento.marcar_enviado_pdv()
    else:
        atendimento.enviado_pdv = True

    _touch_updated_at(atendimento)

    db.commit()

    return _get_atendimento_or_404(db, atendimento_id)


def montar_contexto_receita_impressao(db: Session, atendimento_id: int) -> dict:
    atendimento = _get_atendimento_or_404(db, atendimento_id)

    veterinario = getattr(atendimento, "veterinario", None)
    empresa = getattr(atendimento, "empresa", None)
    pet = getattr(atendimento, "pet", None)
    cliente = getattr(atendimento, "cliente", None)
    prontuario = getattr(atendimento, "prontuario", None)

    receitas = sorted(getattr(atendimento, "receitas", []) or [], key=lambda item: item.id or 0)
    exames = sorted(getattr(atendimento, "exames", []) or [], key=lambda item: item.id or 0)

    observacoes_serializadas = _extrair_observacoes_clinicas_serializadas(
        getattr(prontuario, "observacoes", "") if prontuario else ""
    )

    receitas_descricao = []
    receitas_orientacoes = []
    receitas_completas = []

    for item in receitas:
        descricao = _valor_texto_limpo(getattr(item, "descricao", None))
        orientacoes = _valor_texto_limpo(getattr(item, "orientacoes", None))

        if descricao:
            receitas_descricao.append(descricao)

        if orientacoes:
            receitas_orientacoes.append(orientacoes)

        if descricao or orientacoes:
            receitas_completas.append(
                {
                    "descricao": descricao,
                    "orientacoes": orientacoes,
                }
            )

    if not receitas_descricao and observacoes_serializadas.get("receita"):
        receitas_descricao.append(observacoes_serializadas["receita"])
        receitas_completas.append(
            {
                "descricao": observacoes_serializadas["receita"],
                "orientacoes": "",
            }
        )

    if not receitas_orientacoes and observacoes_serializadas.get("receita"):
        receitas_orientacoes.append(observacoes_serializadas["receita"])
        if not receitas_completas:
            receitas_completas.append(
                {
                    "descricao": "",
                    "orientacoes": observacoes_serializadas["receita"],
                }
            )

    exames_solicitados = []
    for exame in exames:
        texto_exame = _montar_texto_exame(exame)
        if texto_exame:
            exames_solicitados.append(texto_exame)

    if not exames_solicitados and observacoes_serializadas.get("exames"):
        exames_solicitados.append(observacoes_serializadas["exames"])

    diagnostico = ""
    if prontuario and getattr(prontuario, "diagnostico", None):
        diagnostico = _valor_texto_limpo(prontuario.diagnostico)

    data_documento = atendimento.data_fim or atendimento.data_inicio or datetime.utcnow()

    veterinario_nome = _valor_texto_limpo(getattr(veterinario, "nome", None))
    veterinario_crmv = _valor_texto_limpo(getattr(veterinario, "crmv", None))
    veterinario_telefone = _valor_texto_limpo(getattr(veterinario, "telefone", None))
    empresa_logo_url = _resolver_logo_empresa(empresa)
    empresa_endereco_receita = _resolver_endereco_empresa_receita(empresa)

    return {
        "atendimento": atendimento,
        "empresa": empresa,
        "empresa_logo_url": empresa_logo_url,
        "empresa_endereco_receita": empresa_endereco_receita,
        "pet": pet,
        "cliente": cliente,
        "veterinario": veterinario,
        "veterinario_nome": veterinario_nome,
        "veterinario_crmv": veterinario_crmv,
        "veterinario_telefone": veterinario_telefone,
        "prontuario": prontuario,
        "receitas": receitas,
        "receitas_descricao": receitas_descricao,
        "receitas_orientacoes": receitas_orientacoes,
        "receitas_completas": receitas_completas,
        "exames": exames,
        "exames_solicitados": exames_solicitados,
        "diagnostico": diagnostico,
        "data_documento": data_documento,
    }