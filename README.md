# PimpleTV to M3U

Converts [PimpleTV](https://www.pimpletv.ru/) to M3U playlist with AceStream's [HTTP stream](https://wiki.acestream.media/Engine_HTTP_API#API_methods) urls.

Works as Gunicorn server app.

By default AceStream's engine address and port is `127.0.0.1:6878`. This could be set using optional query parameter. E.g.

```url
https://localhost/?10.0.0.1:6878
```

if AceStream is available on `10.0.0.1:6878`.

## Render

App is ready to deploy on [Render](https://render.com/).
