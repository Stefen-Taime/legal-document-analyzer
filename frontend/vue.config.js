module.exports = {
    lintOnSave: false,
    devServer: {
      port: 8080,
      hot: true,
      host: '0.0.0.0',
      client: {
        webSocketURL: 'auto://0.0.0.0:0/ws'
      },
      headers: {
        'Access-Control-Allow-Origin': '*'
      },
      // Ajoutez cette configuration proxy
      proxy: {
        '/api': {
          target: 'http://api:8000',
          pathRewrite: { '^/api': '' },
          changeOrigin: true
        }
      }
    },
    transpileDependencies: []
  }