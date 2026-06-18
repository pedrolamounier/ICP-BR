#!/usr/bin/env python3
import argparse
import datetime as dt
import re
import sys
import unicodedata


def only_digits(value):
    return "".join(ch for ch in value if ch.isdigit())


def strip_accents(value):
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch)
    )


def normalize_ascii_text(value, max_len, allow_space=True):
    value = strip_accents(value).upper().strip()
    value = re.sub(r"\s+", " ", value)
    value = value.replace(",", " ")
    if allow_space:
        value = re.sub(r"[^A-Z0-9 ]", "", value)
    else:
        value = re.sub(r"[^A-Z0-9]", "", value)
    value = value.strip()
    if len(value) > max_len:
        raise ValueError(f"Campo texto excede {max_len} caracteres.")
    return value


def zfill_digits(value, length, field_name):
    value = only_digits(value)
    if len(value) > length:
        raise ValueError(f"{field_name} excede {length} digitos.")
    return value.zfill(length)


def validate_birth_ddmmaaaa(value):
    digits = zfill_digits(value, 8, "Data de nascimento")
    day = int(digits[0:2])
    month = int(digits[2:4])
    year = int(digits[4:8])
    try:
        dt.date(year, month, day)
    except ValueError as exc:
        raise ValueError("Data de nascimento invalida (esperado DDMMAAAA).") from exc
    return digits


def validate_cpf(value):
    cpf = zfill_digits(value, 11, "CPF")
    if cpf == cpf[0] * 11:
        raise ValueError("CPF invalido (todos os digitos iguais).")

    def calc_digit(base, start_weight):
        total = sum(int(num) * weight for num, weight in zip(base, range(start_weight, 1, -1)))
        mod = (total * 10) % 11
        return 0 if mod == 10 else mod

    d1 = calc_digit(cpf[:9], 10)
    d2 = calc_digit(cpf[:10], 11)
    if d1 != int(cpf[9]) or d2 != int(cpf[10]):
        raise ValueError("CPF invalido (digito verificador).")
    return cpf


def build_values(args):
    cpf = validate_cpf(args.cpf)
    nome = normalize_ascii_text(args.nome, 64, allow_space=True)
    nasc = validate_birth_ddmmaaaa(args.nascimento)

    nis = zfill_digits(args.nis, 11, "NIS/PIS/PASEP/CI")
    rg = zfill_digits(args.rg, 15, "RG")
    orgao_uf = normalize_ascii_text(args.orgao_uf, 10, allow_space=False)
    if not orgao_uf:
        raise ValueError("Orgao emissor + UF deve ser informado (ex: SSPRS).")

    cei = zfill_digits(args.cei, 12, "CEI")

    titulo = zfill_digits(args.titulo, 12, "Titulo de Eleitor")
    zona = zfill_digits(args.zona, 3, "Zona")
    secao = zfill_digits(args.secao, 4, "Secao")
    municipio_uf = normalize_ascii_text(args.municipio_uf, 22, allow_space=True)
    if not municipio_uf:
        raise ValueError("MunicipioUF deve ser informado (ex: PORTO ALEGRE RS).")

    oid_136_1 = f"{nasc}{cpf}{nis}{rg}{orgao_uf}"
    oid_136_6 = cei
    oid_136_5 = f"{titulo}{zona}{secao}{municipio_uf}"

    san = (
        f"otherName:2.16.76.1.3.1;UTF8:{oid_136_1},"
        f"otherName:2.16.76.1.3.6;UTF8:{oid_136_6},"
        f"otherName:2.16.76.1.3.5;UTF8:{oid_136_5}"
    )
    cn = f"{nome}:{cpf}"
    return cn, san, cpf, nome


def parse_args():
    parser = argparse.ArgumentParser(
        description="Valida e formata campos ICP-Brasil (PF A3) para SubjectAltName otherName."
    )
    parser.add_argument("--nome", required=True, help="Nome do titular")
    parser.add_argument("--cpf", required=True, help="CPF do titular")
    parser.add_argument("--nascimento", required=True, help="Data de nascimento DDMMAAAA")
    parser.add_argument("--nis", required=True, help="NIS/PIS/PASEP/CI (11 digitos)")
    parser.add_argument("--rg", required=True, help="RG (ate 15 digitos, completa com zeros)")
    parser.add_argument("--orgao-uf", required=True, help="Orgao emissor + UF (max 10), ex: SSPRS")
    parser.add_argument("--cei", required=True, help="CEI (12 digitos)")
    parser.add_argument("--titulo", required=True, help="Titulo de eleitor (ate 12 digitos)")
    parser.add_argument("--zona", required=True, help="Zona eleitoral (ate 3 digitos)")
    parser.add_argument("--secao", required=True, help="Secao eleitoral (ate 4 digitos)")
    parser.add_argument("--municipio-uf", required=True, help="Municipio + UF (max 22)")
    parser.add_argument(
        "--output",
        choices=["san", "cn", "summary"],
        default="san",
        help="Tipo de saida: san, cn ou summary",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        cn, san, cpf, nome = build_values(args)
    except ValueError as exc:
        print(f"Erro de validacao: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.output == "san":
        print(san)
    elif args.output == "cn":
        print(cn)
    else:
        print(f"Nome normalizado: {nome}")
        print(f"CPF validado: {cpf}")
        print(f"CN: {cn}")
        print(f"SAN: {san}")


if __name__ == "__main__":
    main()
