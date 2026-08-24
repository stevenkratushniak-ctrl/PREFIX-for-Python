# Deployment Instructions

## Static Site

The launch site is static and lives in `site/index.html`.

Deploy it with any static host:

- GitHub Pages
- Netlify
- Vercel static
- S3 + CloudFront

## GitHub Pages

1. Create a repo from this product root.
2. Push the contents of `site/` to the Pages publishing branch or publish from `/site`.
3. Set the site root to `/site`.

## VS Code Extension

1. From `editor/vscode`, run `npm install`.
2. Run `npm run build`.
3. Run `npx @vscode/vsce package`.
4. Upload the resulting `.vsix` as a release asset.
5. In marketplace/install guidance, tell users to set `prefixPython.pythonCommand` to a CPython `3.12.x` interpreter when their default `python` is not CPython `3.12.x`.

## Python Package

1. Use CPython `3.12.x`; rc2 was validated on CPython `3.12.6`.
2. Build a wheel and source distribution from the product root.
3. Attach the artifacts to the release.
4. Publish to the chosen Python distribution channel when commercial readiness is approved.
