requirejs.config({
  baseUrl: "static/scripts",
  paths: {
    angular: "../bower_components/angular/angular",
    jquery: "../bower_components/jquery/jquery",
    JSXTransformer: "../bower_components/react/JSXTransformer",
    jsx: "../bower_components/require-jsx/jsx",
    react: "../bower_components/react/react"
  },
  shim: {
    angular: {
      exports: 'angular'
    }
  },
  packages: [
    {
      name: 'cs',
      location: '../bower_components/require-cs',
      main: 'cs'
    }, {
      name: 'coffee-script',
      location: '../bower_components/coffee-script',
      main: 'index'
    }
  ]
});

require(["cs!main"]);
