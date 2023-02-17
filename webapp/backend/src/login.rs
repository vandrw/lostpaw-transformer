use std::time::{Duration, Instant};

use anyhow::{anyhow, ensure, Result};
use dashmap::DashMap;
use openidconnect::core::{CoreAuthenticationFlow, CoreClient, CoreProviderMetadata};
use openidconnect::url::Url;
use openidconnect::{
    AccessTokenHash, AuthorizationCode, ClientId, ClientSecret, CsrfToken, IssuerUrl, Nonce,
    OAuth2TokenResponse, PkceCodeChallenge, PkceCodeVerifier, RedirectUrl, Scope, TokenResponse,
};

use openidconnect::reqwest::async_http_client;

pub struct UserAuthenticator {
    client: CoreClient,
    ongoing_authentifications: DashMap<String, AuthenticationContext>,
}

impl UserAuthenticator {
    pub async fn new() -> Result<Self> {
        let provider_metadata = CoreProviderMetadata::discover_async(
            IssuerUrl::new("https://accounts.google.com".to_string())?,
            async_http_client,
        )
        .await?;
        Ok(Self {
            client: CoreClient::from_provider_metadata(
                provider_metadata,
                ClientId::new("token".to_string()),
                Some(ClientSecret::new("secret-token".to_string())),
            )
            // Set the URL the user will be redirected to after the authorization process.
            .set_redirect_uri(RedirectUrl::new(
                "http://127.0.0.1:5173/login/confirm".to_string(),
            )?),
            ongoing_authentifications: DashMap::new(),
        })
    }

    pub fn new_auth_context(&self) -> Result<AuthenticationContext> {
        // Generate a PKCE challenge.
        let (pkce_challenge, pkce_verifier) = PkceCodeChallenge::new_random_sha256();

        // Generate the full authorization URL.
        let (auth_url, csrf_token, nonce) = self
            .client
            .authorize_url(
                CoreAuthenticationFlow::AuthorizationCode,
                CsrfToken::new_random,
                Nonce::new_random,
            )
            // Set the desired scopes.
            .add_scope(Scope::new("email".to_string()))
            .add_scope(Scope::new("profile".to_string()))
            // Set the PKCE code challenge.
            .set_pkce_challenge(pkce_challenge)
            .url();

        Ok(AuthenticationContext::new(
            pkce_verifier,
            csrf_token,
            nonce,
            auth_url,
        ))
    }

    pub fn init_login(&self) -> Result<Url> {
        let ctx = self.new_auth_context()?;
        let key = ctx.csrf_token.secret().clone();
        let url = ctx.auth_url.clone();
        self.ongoing_authentifications.insert(key, ctx);
        Ok(url)
    }

    pub async fn login(&self, state: &str, code: &str) -> Result<String> {
        let (_, ctx) = self
            .ongoing_authentifications
            .remove(state)
            .ok_or_else(|| anyhow!("invalid state parameter"))?;

        self.login_with_context(ctx, state, code).await
    }

    pub async fn login_with_context(
        &self,
        context: AuthenticationContext,
        state: &str,
        code: &str,
    ) -> Result<String> {
        // Verify that the `state` parameter returned by the server matches
        // `csrf_state`.
        ensure!(context.csrf_token.secret() == state);

        // Now you can exchange it for an access token and ID token.
        let token_response = self
            .client
            .exchange_code(AuthorizationCode::new(code.to_string()))
            // Set the PKCE code verifier.
            .set_pkce_verifier(context.pkce_verifier)
            .request_async(async_http_client)
            .await?;

        // Extract the ID token claims after verifying its authenticity and nonce.
        let id_token = token_response
            .id_token()
            .ok_or_else(|| anyhow!("Server did not return an ID token"))?;
        let claims = id_token.claims(&self.client.id_token_verifier(), &context.nonce)?;

        // Verify the access token hash to ensure that the access token hasn't
        // been substituted for another user's.
        if let Some(expected_access_token_hash) = claims.access_token_hash() {
            let actual_access_token_hash = AccessTokenHash::from_token(
                token_response.access_token(),
                &id_token.signing_alg()?,
            )?;
            if actual_access_token_hash != *expected_access_token_hash {
                return Err(anyhow!("Invalid access token"));
            }
        }

        let email = claims
            .email()
            .map(|email| email.as_str())
            .unwrap_or("<not provided>");

        // The authenticated user's identity is now available. See the IdTokenClaims struct for a
        // complete listing of the available claims.
        println!(
            "User {} with e-mail address {} has authenticated successfully",
            claims.subject().as_str(),
            email
        );

        dbg!(claims);
        Ok(email.to_owned())
    }

    pub fn clear_old_authentifications(&self, age_threshold: Duration) {
        let threshold = Instant::now() - age_threshold;
        self.ongoing_authentifications
            .retain(|_, ctx| ctx.created > threshold)
    }
}

pub struct AuthenticationContext {
    pub auth_url: Url,
    pkce_verifier: PkceCodeVerifier,
    csrf_token: CsrfToken,
    nonce: Nonce,
    created: Instant,
}

impl AuthenticationContext {
    pub fn new(
        pkce_verifier: PkceCodeVerifier,
        csrf_token: CsrfToken,
        nonce: Nonce,
        auth_url: Url,
    ) -> Self {
        Self {
            pkce_verifier,
            csrf_token,
            nonce,
            auth_url,
            created: Instant::now(),
        }
    }
}
