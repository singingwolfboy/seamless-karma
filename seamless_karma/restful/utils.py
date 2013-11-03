from flask.ext.restful import reqparse

# argument subclass that can handle parsing dicts
class Argument(reqparse.Argument):
    def parse(self, request):
        """Parses argument value(s) from the request, converting according to
        the argument's type.

        :param request: The flask request object to parse arguments from
        """
        source = self.source(request)

        results = []

        for operator in self.operators:
            name = self.name + operator.replace("=", "", 1)
            if name in source:
                # Account for MultiDict and regular dict
                if hasattr(source, "getlist"):
                    values = source.getlist(name)
                else:
                    values = [source.get(name)]

                for value in values:
                    if not self.case_sensitive:
                        value = value.lower()
                    if self.choices and value not in self.choices:
                        self.handle_validation_error(ValueError(
                            u"{0} is not a valid choice".format(value)))
                    try:
                        value = self.convert(value, operator)
                    except Exception as error:
                        if self.ignore:
                            continue

                        self.handle_validation_error(error)

                    results.append(value)

        if not results and self.required:
            if isinstance(self.location, six.string_types):
                error_msg = u"{0} is required in {1}".format(
                    self.name,
                    self.location
                )
            else:
                error_msg = u"{0} is required in {1}".format(
                    self.name,
                    ' or '.join(self.location)
                )
            self.handle_validation_error(ValueError(error_msg))

        if not results:
            return self.default

        if self.action == 'append':
            return results

        if self.action == 'store' or len(results) == 1:
            return results[0]
        return results
