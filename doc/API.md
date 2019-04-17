# Overview

This specification defines a protocol of data interchange between Magicchain
Payment Server (hereinafter just SERVER, capitalized) and its counterparty.
SERVER is a part of MagicChain project.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in RFC 2119.

# TODO: section title

The protocol is based on JSON-RPC 2.0 with HTTP/1.x used as a transport. Both
ends of communication MUST implement JSON-RPC 2.0 server since SERVER sends
notifications to its counterparty. There MUST be exactly one counterparty with
static IP-address which is stored in the SERVER's configuration file. In
contrast, single counterparty MAY communicate with multiple SERVERs.

TODO: url 

TODO: POST, Content-Type

TODO: Both positional and named parameters are accepted.

# Security

Both directions of communication between SERVER and its counterparty are
protected from malicious modifications and duplications with HMAC signatures.

The same HMAC key is used for both directions of communication. There's no
need to use separate keys since compromising of any end of communication
would leak both keys anyway.

## From SERVER to counterparty

All HTTP responses and HTTP requests with non-empty body sent from SERVER
to its counterparty are signed with HMAC-SHA256 algorithm:

1. NONCE value is generated as a number of milliseconds passed since Unix Epoch.
2. The key for HMAC-SHA256 algorithm is taken from the configuration file.
3. NONCE value in decimal form is appended to the request/response body without
   a delimiter, HMAC-SHA256 signature of the resulting string is calculated.
4. The following three fields are added to the HTTP request/response header:
    - HMAC-Signature: the result of HMAC-SHA256 algorithm in hex form;
    - HMAC-Nonce: the NONCE value;
    - HMAC-KeyId: an arbitrary string identifier stored in the configuration
      file. It may be used by the counterpart to choose an appropriate HMAC key
      if the counterpart works with several instances of SERVER.

## From counterparty to SERVER

All HTTP responses and HTTP requests with non-empty body sent to SERVER from
its counterparty MUST be signed with HMAC-SHA256 algorithm. The following
checks are made:

1. NONCE value is extracted from `HMAC-Nonce` HTTP header field. The value MUST
   belong to the range `[SERVER TIME - 60000ms; SERVER TIME + 60000ms]`. If the
   NONCE value is out of the range, `403 Forbidden` HTTP error is returned.
2. NONCE value in decimal form is appended to the request/response body without
   a delimiter, HMAC-SHA256 signature of the resulting string is calculated.
   The result is compared with the value of the `HMAC-Signature` header field 
   If it doesn't match, `403 Forbidden` HTTP error is returned.

HTTP responses and HTTP requests with empty body (only responses to JSON-RPC
notifications match this condition) MAY be sent without a signature.

# Configuration file

Name of configuration file is determined in the following order:

1. Value of environment variable `MC_PAYMENT_CONFIG` provided it's present.
2. `$HOME/.magicchain/payment.conf` provided HOME environment variable is set
   and such file exists.
3. `/etc/magicchain/payment.conf`

TODO: structure, example

# Deposit-related API

## `get-address` method

This API call is used to create/query for deposit address of the specified user.
The address is returned immediately (synchronously) if it was generated earlier.
Otherwise the address is sent asynchronously within `address` notification.

### Parameters

- `userid` - numeric user id;
- `coin` - name of coin (case insensitive).

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

## `address` notification

This notification is sent to the counterparty when asynchronous deposit address
generation is finished. For ETH and ETH-based tokens it means that a child
contract is deployed (which can take some amount of time).

### Parameters (named)

- `userid` - numeric user id;
- `coin` - coin name;
- `address` - the address.

### Expected result

No result is expected since it's a notification in terms of JSON RPC 2.0. This
notification MAY be lost for some reason, so the counterparty SHOULD repeat the
`get-address` request until the address is returned (probably, synchronously,
if notification was sent but not delivered properly).

## `deposit` notification

Technically, it's not a notification in terms of JSON RPC 2.0. It's a request
which requires a response. It's sent from SERVER to its counterparty when
a deposit is detected.

### Parameters (named)

- `userid` - numeric user id;
- `coin` - name of coin;
- `amount` - value of deposit in atomic units, 1 for non-fungible tokens;
- `tokenId` - id of token, null for fungible tokens.

### Expected result

Boolean value `true` signifies that the deposit was accepted by the counterparty.
In any other case (including an absence of any reply) the counterparty would be
notified again later.

# Hot wallet related API

## `send` method

All `send` requests are performed asynchronously. The counterparty assigns a
unique id (UUID) of the send request. When the request is finished, a
notification is sent to the counterparty with information about transaction
(including - but not limited to - transaction hash and block height).

### Parameters

- `uuid` - UUID of the request, can be used in `get-send-status` request,
  included into `tx-confirmed` notification;
- `coin` - coin name;
- `amount` - value of transfer in atomic units, 1 for non-fungible tokens;
  passed as string in decimal form.
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

## TODO: more specific send-like requests

## `get-tx-status` method

This is a polling version of `tx-confirmed` notification. In any case it
returns immediately.

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
            "txhash": "0x85235f1a6438b97742d042d3ee1380ecc49fbae29d4a8270cb81088f55f9ebbc",
            "height": 7654321,
            "confirmed": true
        }
    }

### Response (transaction is not confirmed)

    {
        "jsonrpc": "2.0",
        "id": 1,
        "result":
        {
            "uuid": "394b7137-8b8e-4f87-b95e-ddb5b516232f",
            "confirmed": false
        }
    }

## `estimate-fee` method

This method is used to calculate a fee of a particular request without issuing
a transaction. There's NO GUARANTEE that the returned value stays valid for
any amount of time.

### Parameters

- `request-name` - name of request;
- `request-params` - all parameters of the request except uuid.

Example:

    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "estimate-fee",
        "params":
        {
            "request-name": "send",
            "request-params":
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

## `tx-confirmed` notification

This notification is sent when some transaction issued by the SERVER is finally
confirmed. No response is expected. If the notification is not delivered to the
counterparty for some reason, it will NOT be sent again. That's why "polling
version" of this notification does exist (`get-tx-status` request).

### Parameters (named)

- `uuid` - UUID of send request;
- `txhash` - hash of the transaction;
- `height` - height of block which includes the transaction.

# Miscelanneous API

## `get-status` method

TODO: balance of deposit master (creator of sub-contracts)

TODO: balance of the hot wallet

TODO: number of pending address requests

TODO: number of pending send (and other) requests

TODO: status of node(s)

TODO: gas price(s)