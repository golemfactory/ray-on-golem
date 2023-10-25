from typing import Dict, List, Set

PROVIDERS_BLACKLIST: Dict[str, Set[str]] = {
    "polygon": {
        "0xc04863f26dab1bb0d9ec35c793b01c6cc5e7a399",
        "0xfc88946eac7433315a82a0d83cef54493aa69948",
        "0xa272d86f5c0466783ecff3403786f42d18f3fc3b",
        "0x51fb0db558d9c50cae94cbbeeec4a9e55898886f",
        "0x5595546699e894cf077685a20f3ff214a217b950",
        "0x0bd56a416463d467e4e79dcf72f81b4e9ffcb924",
        "0x07cde3150460db9d148fa17360c273f1efecc258",
        "0x56c64723db51cd76eccc2098f3f05eaefd53f720",
        "0x65cffc710ff26ca593426f1669d31de84d156043",
        "0x4321552531b91f7c58b5e7d24ff083c92f8465e0",
        "0x37792f405c68a2bcee144cc9b6b5f3efabd3984d",
        "0x4bd46f8e1ed87dbfafae9293ef2aeff1fe2818a1",
        "0x1ce39f1bfb8ef5282071924a83a9b6a0359ca3c9",
        "0x1371e45b1037460b17892635e2870cfe84c4545f",
        "0x43c7383abf784186e5bc94aa22408e7768148b98",
    }
}

PROVIDERS_SCORED: Dict[str, List[str]] = {
    "polygon": [
        "0x7d529a5b0b58400d09154b47d94ee022ba7658cc",
    ]
}
