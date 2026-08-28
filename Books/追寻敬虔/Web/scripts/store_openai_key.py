#!/usr/bin/env python3
"""Safely replace the reader's OpenAI API key in macOS Keychain.

The macOS ``security add-generic-password -w`` interactive prompt truncates
long input at 128 characters. Current project API keys can be longer, so this
helper reads the secret with Python's non-echoing prompt and updates the
existing Keychain item through Security.framework.
"""

from __future__ import annotations

import argparse
import ctypes
import getpass
import platform
import sys
from dataclasses import dataclass


DEFAULT_ACCOUNT = "qfg-reader"
DEFAULT_SERVICE = "org.openai.qfg-reader"
ERR_SEC_SUCCESS = 0
ERR_SEC_ITEM_NOT_FOUND = -25300


class KeychainError(RuntimeError):
    """Raised when the macOS Keychain operation fails."""


@dataclass(frozen=True)
class KeychainLibraries:
    security: ctypes.CDLL
    core_foundation: ctypes.CDLL


def load_keychain_libraries() -> KeychainLibraries:
    if platform.system() != "Darwin":
        raise KeychainError("This helper is only available on macOS.")

    security = ctypes.CDLL(
        "/System/Library/Frameworks/Security.framework/Security"
    )
    core_foundation = ctypes.CDLL(
        "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
    )

    security.SecKeychainFindGenericPassword.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_char_p,
        ctypes.c_uint32,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    security.SecKeychainFindGenericPassword.restype = ctypes.c_int32
    security.SecKeychainItemModifyAttributesAndData.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    security.SecKeychainItemModifyAttributesAndData.restype = ctypes.c_int32
    security.SecKeychainItemFreeContent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    security.SecKeychainItemFreeContent.restype = ctypes.c_int32
    core_foundation.CFRelease.argtypes = [ctypes.c_void_p]
    core_foundation.CFRelease.restype = None
    return KeychainLibraries(security, core_foundation)


def find_generic_password_item(
    libraries: KeychainLibraries, account: str, service: str
) -> ctypes.c_void_p:
    account_bytes = account.encode("utf-8")
    service_bytes = service.encode("utf-8")
    item_ref = ctypes.c_void_p()
    status = libraries.security.SecKeychainFindGenericPassword(
        None,
        len(service_bytes),
        service_bytes,
        len(account_bytes),
        account_bytes,
        None,
        None,
        ctypes.byref(item_ref),
    )
    if status == ERR_SEC_ITEM_NOT_FOUND:
        raise KeychainError(
            f'No generic password exists for account "{account}" and service "{service}". '
            "Create the placeholder item described in README-zh.md first."
        )
    if status != ERR_SEC_SUCCESS or not item_ref.value:
        raise KeychainError(f"Unable to find the Keychain item (OSStatus {status}).")
    return item_ref


def update_generic_password(account: str, service: str, secret: str) -> None:
    libraries = load_keychain_libraries()
    item_ref = find_generic_password_item(libraries, account, service)
    secret_bytes = secret.encode("utf-8")
    secret_buffer = ctypes.create_string_buffer(secret_bytes)
    try:
        status = libraries.security.SecKeychainItemModifyAttributesAndData(
            item_ref,
            None,
            len(secret_bytes),
            ctypes.cast(secret_buffer, ctypes.c_void_p),
        )
        if status != ERR_SEC_SUCCESS:
            raise KeychainError(f"Unable to update the Keychain item (OSStatus {status}).")
    finally:
        ctypes.memset(secret_buffer, 0, len(secret_buffer))
        libraries.core_foundation.CFRelease(item_ref)


def read_generic_password(account: str, service: str) -> str:
    libraries = load_keychain_libraries()
    account_bytes = account.encode("utf-8")
    service_bytes = service.encode("utf-8")
    password_length = ctypes.c_uint32()
    password_data = ctypes.c_void_p()
    item_ref = ctypes.c_void_p()
    status = libraries.security.SecKeychainFindGenericPassword(
        None,
        len(service_bytes),
        service_bytes,
        len(account_bytes),
        account_bytes,
        ctypes.byref(password_length),
        ctypes.byref(password_data),
        ctypes.byref(item_ref),
    )
    if status != ERR_SEC_SUCCESS:
        raise KeychainError(f"Unable to verify the Keychain item (OSStatus {status}).")
    try:
        return ctypes.string_at(password_data, password_length.value).decode("utf-8")
    finally:
        libraries.security.SecKeychainItemFreeContent(None, password_data)
        if item_ref.value:
            libraries.core_foundation.CFRelease(item_ref)


def validate_secret(secret: str) -> None:
    if not secret.startswith("sk-"):
        raise KeychainError('The value must be a complete OpenAI secret beginning with "sk-".')
    if len(secret) < 20:
        raise KeychainError("The OpenAI secret is unexpectedly short.")
    if any(character.isspace() for character in secret):
        raise KeychainError("The OpenAI secret must not contain whitespace.")
    if not secret.isascii():
        raise KeychainError("The OpenAI secret must contain only ASCII characters.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", default=DEFAULT_ACCOUNT)
    parser.add_argument("--service", default=DEFAULT_SERVICE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        secret = getpass.getpass("Paste the complete OpenAI API Key: ")
        confirmation = getpass.getpass("Paste it again to confirm: ")
        if secret != confirmation:
            raise KeychainError("The two values do not match; the Keychain was not changed.")
        validate_secret(secret)
        print(f"Key length: {len(secret)}; suffix: {secret[-4:]}")
        update_generic_password(args.account, args.service, secret)
        stored = read_generic_password(args.account, args.service)
        if stored != secret:
            raise KeychainError("Keychain verification failed; the stored value differs.")
        print(f"Saved and verified {len(stored)} characters; suffix: {stored[-4:]}")
        return 0
    except (KeychainError, UnicodeError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
