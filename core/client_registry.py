CLIENTS = {
    "dofamin": {
        "name": "DOFAMIN",
        "folder": "dofamin",
        "instagram_account_id_env": "DOFAMIN_INSTAGRAM_ACCOUNT_ID",
        "instagram_access_token_env": "DOFAMIN_INSTAGRAM_ACCESS_TOKEN",
        "verify_token_env": "DOFAMIN_VERIFY_TOKEN",
    },

    "altamare": {
        "name": "Altamare",
        "folder": "altamare",
        "instagram_account_id_env": "ALTAMARE_INSTAGRAM_ACCOUNT_ID",
        "instagram_access_token_env": "ALTAMARE_INSTAGRAM_ACCESS_TOKEN",
        "verify_token_env": "ALTAMARE_VERIFY_TOKEN",
    },

    "energy_fitness": {
        "name": "ENERGY Fitness",
        "folder": "energy_fitness",
        "instagram_account_id_env": "ENERGY_INSTAGRAM_ACCOUNT_ID",
        "instagram_access_token_env": "ENERGY_INSTAGRAM_ACCESS_TOKEN",
        "verify_token_env": "ENERGY_VERIFY_TOKEN",
    },

    "vizaje_nica": {
        "name": "Vizaje Nica",
        "folder": "vizaje_nica",
        "instagram_account_id_env": "VIZAJE_NICA_INSTAGRAM_ACCOUNT_ID",
        "instagram_access_token_env": "VIZAJE_NICA_INSTAGRAM_ACCESS_TOKEN",
        "verify_token_env": "VIZAJE_NICA_VERIFY_TOKEN",
    },
}


def get_client(client_id: str) -> dict | None:
    return CLIENTS.get(client_id)


def get_client_by_instagram_account_id(
    instagram_account_id: str,
    env_values: dict,
) -> tuple[str, dict] | tuple[None, None]:

    for client_id, client in CLIENTS.items():
        env_name = client["instagram_account_id_env"]
        configured_id = env_values.get(env_name)

        if configured_id == instagram_account_id:
            return client_id, client

    return None, None