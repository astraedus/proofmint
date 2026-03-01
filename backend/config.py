from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    hedera_account_id: str = ""
    hedera_private_key: str = ""
    hedera_topic_id: str = ""        # HCS topic (created on first use if empty)
    hedera_nft_token_id: str = ""    # NFT collection (created on first use if empty)
    hedera_network: str = "testnet"
    gemini_api_key: str = ""
    github_token: str = ""
    database_url: str = "sqlite+aiosqlite:///proofmint.db"

    class Config:
        env_file = ".env"


settings = Settings()
