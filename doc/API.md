# Overview

This specification defines a protocol of data interchange between Magicchain
Payment Server (hereinafter just SERVER, capitalized) and its counterparty.
SERVER is a part of MagicChain project.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in RFC 2119.

# Basics

The protocol is based on JSON-RPC 2.0 with HTTP/1.x used as a transport. SERVER
doesn't send any requests to its counterparties, it just responds to their
requests.

All RPC requests MUST be sent to HTTP URL: `http://.../mc/v1/api` using POST
method. Content-Type header field MUST be set to `application/json`.

Both positional and named parameters of JSON-RPC requests are supported by the
SERVER.

# Security

Both directions of communication between SERVER and its counterparty (requests
and responses) are protected from malicious modification by HMAC signatures.

Protection from malicious request duplication is either unnecessary or ensured
by the nature of data passed.

Protection from malicious response duplication MAY be ensured by using unique
JSON RPC request id for each request (e.g. UUID).

The same HMAC key is used for both directions of communication. There's no
need to use separate keys since compromising of any end of communication
would leak both keys anyway.

## From SERVER to counterparty

All HTTP responses with non-empty body sent from SERVER to its counterparty
are signed with HMAC-SHA256 algorithm:

1. The key for HMAC-SHA256 algorithm is taken from the configuration file.
2. HMAC-SHA256 signature of the body is calculated.
3. The following two fields are added to the HTTP request/response header:
    - HMAC-Signature: the result of HMAC-SHA256 algorithm in hex form;
    - HMAC-KeyId: an arbitrary string identifier stored in the configuration
      file. It may be used by the counterparty to choose an appropriate HMAC
      key if the counterparty works with several instances of SERVER.

## From counterparty to SERVER

All HTTP requests with non-empty body sent to SERVER from its counterparty
MUST be signed with HMAC-SHA256 algorithm.

HMAC-SHA256 signature of request/response body is calculated. The result is
compared with the value of the `HMAC-Signature` header field. If request
signature doesn't match, `403 Forbidden` HTTP error is returned. If response
signature doesn't match, the response is just ignored.

# Configuration file

Name of configuration file is determined in the following order:

1. Value of environment variable `MC_PAYMENT_CONFIG` provided it's present.
2. `$HOME/.magicchain/payment.conf` provided HOME environment variable is set
   and such file exists.
3. `/etc/magicchain/payment.conf`

Here's an example of configuration file:

    {
        "security":
        {
            "hmac-key": "ac21f2c131b112381e75f1d490d39546bf80e862eeb6d264e67cc4161b9bb0e6",
            "hmac-keyid": "7d6830d9"
        },
        "database":
        {
            "driver": "mysql",
            "host": "127.0.0.1",
            "user": "mcpayment",
            "password": "mcpayment",
            "dbname": "mcpayment"
        },
        "nodes":
        [
            {
                "chainId": "ETH-ropsten",
                "address": "127.0.0.1",
                "port": 8545
            }
        ],
        "Ethereum":
        [
            {
                "chainId": "ETH-ropsten",
                "symbol": "ROPSTEN",
                "depositContract": "0xf862ed9639040315c5c66234fcba1cb9bd80739d",
                "depositController": "0xbbc887fdeeba38f1ebbdae6d07908a104e543da4",
                "hotWallet": "0x864faf6156947c730a49c11abf5843c5d304c257",
                "ERC223":
                [
                    {
                        "symbol": "ROPSTEN:MAGI",
                        "contract": "0xdca7faefd26b87a0f5e9d9814b3372819ffd46b9"
                    }
                ],
                "ERC721":
                [
                    {
                        "symbol": "ROPSTEN:MCI",
                        "contract": "0x0bead51721ad217311eb97975ce526446346b998",
                        "extAPI":
                        [
                            {
                                "name": "ROPSTEN_MCI_setTokenContent",
                                "type": "sendTransaction",
                                "sender": "0x068dC580b637D8D2A6C0Bae6c273C5Ff39073833",
                                "args": ["uint256", "address", "uint256", "uint256", "uint256", "uint256", "uint256"],
                                "selector": "8447d0cc"
                            },
                            {
                                "name": "ROPSTEN_MCI_mint",
                                "type": "sendTransaction",
                                "sender": "0x068dC580b637D8D2A6C0Bae6c273C5Ff39073833",
                                "args": ["address", "uint256", "uint256", "uint256", "uint256", "uint256"],
                                "selector": "299bada0",
                                "customResult": "MCI_mint"
                            },
                            {
                                "name": "ROPSTEN_MCI_tokenContent",
                                "type": "call",
                                "args": ["uint256"],
                                "selector": "3969a1a5",
                                "customResult": "MCI_tokenContent"
                            }
                        ]
                    }
                ]
            }
        ]
    }

ERC-223 and ERC-721 tokens supported by the SERVER are configurable.

# Deposit-related API

## `get-address` method

This API call is used to create/query for deposit address of the specified user.
The address is returned immediately (synchronously) if it was generated earlier.

### Parameters

- `userid` - numeric user id;
- `coin` - name of coin (case sensitive).

Example:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "get-address",
        "params":
        {
            "userid": 666,
            "coin": "ETH"
        }
    }

### Response (the address is known already)

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        {
            "pending": false,
            "userid": 666,
            "coin": "ETH",
            "address": "0x448ea34ce73f656b38d8e5bd83b5c88f901b4a17"
        }
    }

### Response (the address is not generated yet)

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        {
            "pending": true
        }
    }

## `list-deposits` method

This API call is used to get a list of incoming payments (deposits). All
deposits are numbered (1-based) in order of detection. This method returns
limited list of deposits starting from the specified sequential number.

### Parameters

- `start` - sequential number of the first returned deposit (default: 1);
- `limit` - number of returned deposits (default: 25).

Example:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "list-deposits",
        "params":
        {
            "start": 1
        }
    }

### Response:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        [
            {
                "amount": null,
                "blockNumber": 8280928,
                "coin": "MCI",
                "no": 1,
                "tokenContent":
                [
                    "0x0000000000000000000000000000000000000000000000000000000000000001",
                    "0x0000000000000000000000000000000000000000000000000000000000000002",
                    "0x0000000000000000000000000000000000000000000000000000000000000003",
                    "0x0000000000000000000000000000000000000000000000000000000000000004",
                    "0x0000000000000000000000000000000000000000000000000000000000000005"
                ],
                "tokenId": "0x0000000000000000000000000000000000000000000000000000000000000001",
                "txid": "0x51485066c747e5018abf621a693c3e505ec0dcc3aebf1c3c5e1b39c8fe51812e",
                "userid": 666,
                "vout": 7
            },
            {
                "amount": "0xde0b6b3a7640000",
                "blockNumber": 8281272,
                "coin": "ETH",
                "no": 2,
                "tokenContent": null,
                "tokenId": null,
                "txid": "0x62ea439baf5d147f71cf9c8a9913ca67e2c7581c9dc9cd4fd54773c2ddd373fb",
                "userid": 666,
                "vout": 15
            }
        ]
    }

Notes:

- `amount` is `null` for non-fungible (e.g. ERC721) tokens; for fungible tokens
(ETH, ERC223 tokens etc...) amount is expressed in atomic units (e.g. wei for
ETH);
- `tokenId` is `null` for fungible tokens;
- `tokenContent` is MCI-specific field containing 5 integers describing MCI
token content; it's `null` for all other coins;
- `vout` along with `txid` uniquely identifies a payment within blockchain;
`txid` alone can't be used to identify payment since single transaction may
perform several payments.

# Hot wallet related API

## `send` method

All `send` (and send-like) requests are performed asynchronously. The
counterparty assigns a unique id (UUID) of the send request. Status of
the request execution can be checked with `get-tx-status` request using
the unique id.

### Parameters

- `uuid` - UUID of the request, can be used in `get-tx-status` request;
- `coin` - coin name;
- `amount` - value of transfer in atomic units, null for non-fungible tokens;
  if not null, MUST be passed as string in decimal or hexadecimal (with prefix
  0x) form;
- `tokenId` - id of token, null for fungible tokens;
- `recipient` - destination address of transfer.

Example:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "send",
        "params":
        {
            "uuid": "394b7137-8b8e-4f87-b95e-ddb5b516232f",
            "coin": "ETH",
            "amount: "1000000000000000000",
            "tokenId": null,
            "recipient": "0x26a956cd55a99b2a57b5be963a931b69d3d11c98"
        }
    }

### Response (success)

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result": null
    }

### Response (insufficient funds)

TODO

### Response (duplicate uuid)

TODO

### Security considerations

Replay attack is not efficient since sending the same request will end up with
"duplicate uuid" error.

## `MCI_setTokenContent` method

This method is Magicchain-specific. It's used to call `setTokenContent` function
of the MagicChain721 contract instance. In many aspects it resembles `send`
request:

- it's asynchronous;
- it has UUID;
- its status may be polled with `get-tx-status` method;
- required fee may be estimated with `estimate-fee` method.

### Parameters

- `uuid` - UUID of the request, can be used in `get-tx-status` request;
- `args` - array of arguments of `setTokenContent` function. `uint256` arguments
  MUST be passed as strings in decimal or hexadecimal (with prefix `0x`) form.
  Fixed-length arrays must be passed inlined (i.e. `uint256[2]` as two `uint256`
  values).

### Response

See `send` method above.

## `MCI_mint` method

This method is Magicchain-specific. It's used to call `mint` function of the
MagicChain721 contract instance.

### Parameters

- `uuid` - UUID of the request, can be used in `get-tx-status` request;
- `args` - array of arguments of `mint` function. `uint256` arguments MUST be
  passed as strings in decimal or hexadecimal (with prefix `0x`) form. `string`
  arguments are passed as is (respecting JSON escaping rules). Fixed-length
  arrays must be passed inlined (i.e. `uint256[2]` as two `uint256` values).

### Response

See `send` method above.

## `MCI_tokenContent` method

This method is Magicchain-specific. It's used to call `tokenContent` function
of the MagicChain721 contract instance without transaction invocation (using
`eth_call` Ethereum API). Result is returned immediately.

### Parameters

- `args` - array of arguments of `tokenContent` function.

Example:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "MCI_tokenContent",
        "params":
        [
            [
                "1"
            ]
        ]
    }

### Response

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        [
            "0x0000000000000000000000000000000000000000000000000000000000000001",
            "0x0000000000000000000000000000000000000000000000000000000000000002",
            "0x0000000000000000000000000000000000000000000000000000000000000003",
            "0x0000000000000000000000000000000000000000000000000000000000000004",
            "0x0000000000000000000000000000000000000000000000000000000000000005"
        ]
    }

## `get-tx-status` method

Returns status of previously sent send-like request (`send`,
`MCI_setTokenContent`, `MCI_mint`).

### Parameters

- `uuid` - UUID of request.

Example:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "get-tx-status",
        "params":
        {
            "uuid": "394b7137-8b8e-4f87-b95e-ddb5b516232f"
        }
    }

### Response (transaction is confirmed)

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        {
            "uuid": "394b7137-8b8e-4f87-b95e-ddb5b516232f",
            "result":
            {
                "txhash": "0x85235f1a6438b97742d042d3ee1380ecc49fbae29d4a8270cb81088f55f9ebbc"
            },
            "confirmed": true,
            "error": null,
            "pending": false
        }
    }

### Response (`MCI_mint` specific)

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        {
            "uuid": "ac424963-e81b-4537-a6de-6d8f5be9cb07",
            "result":
            {
                "tokenId": "0x0000000000000000000000000000000000000000000000000000000000000001",
                "txhash": "0x51485066c747e5018abf621a693c3e505ec0dcc3aebf1c3c5e1b39c8fe51812e"
            },
            "confirmed": true,
            "error": null,
            "pending": false
        }
    }

### Response (transaction is not confirmed)

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        {
            "uuid": "394b7137-8b8e-4f87-b95e-ddb5b516232f",
            "confirmed": false,
            "error": null,
            "pending": true
        }
    }

## `estimate-fee` method

This method is used to calculate a fee of a particular request without issuing
a transaction. There's NO GUARANTEE that the returned value stays valid for
any amount of time.

### Parameters

- `requestname` - name of request;
- `requestparams` - all parameters of the request except uuid.

Example:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "estimate-fee",
        "params":
        {
            "requestname": "send",
            "requestparams":
            {
                "coin": "ETH",
                "amount: "1000000000000000000",
                "tokenId": null,
                "recipient": "0x26a956cd55a99b2a57b5be963a931b69d3d11c98"
            }
        }
    }

### Response

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        {
            "ETH": "105000000000000"
        }
    }

