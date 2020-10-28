from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def site_configuration_value(context, name):
    """
    Retrieve Configuration value for the key specified as name argument.

    Arguments:
        context (dict): Context of current request.
        name (str): Name of the key for which to return configuration value.

        Returns:
            Configuration value for the given key or returns `None` if default is not available.
    """
    request = context['request']
    site_configuration = request.site.siteconfiguration
    return site_configuration.get_edly_configuration_value(name)
