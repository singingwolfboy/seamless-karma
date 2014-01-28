({
  //appDir: "seamless_karma/static",
  mainConfigFile: "seamless_karma/static/scripts/amd.config.js",
  baseUrl: "seamless_karma/static/scripts",
  out: "seamless_karma/static/scripts/optimized.js",
  name: "../bower_components/almond/almond",
  include: "amd.config",
  optimize: "uglify2",
  generateSourceMaps: true,
  preserveLicenseComments: false
})