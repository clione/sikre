import json

import falcon

from sikre import settings
from sikre.utils.logs import logger
from sikre.models.users import User
from sikre.models.items import Category, Item
from sikre.models.services import Service
from sikre.resources.auth.decorators import login_required
from sikre.resources.auth.utils import parse_token


class Items(object):

    @falcon.before(login_required)
    def on_get(self, req, res):
        """Get the items that belong to that user.

        This method contains two behaviours, one returns
        Handle the GET request, returning a list of the items that the user
        has access to.

        First we create an empty dictionary and query the database to get
        all the item objects. After that, we iterate over the objects to
        populate the dictionary. In the end we return a 200 code to the browser
        and return the results dictionary wrapped in a list like the REsT
        standard says.
        """
        payload = {}
        # Parse token and get user id
        user_id = parse_token(req)['sub']

        try:
            # Get the user
            user = User.get(User.id == int(user_id))
            # See if we have to filter by category
            filter_category = req.get_param("category", required=False)
            if filter_category:
                # Get the category
                category = (Category.select(Category.name, Category.id)
                                  .where(Category.id == int(filter_category))
                                  .get())
                payload["category_name"] = str(category.name)
                payload["category_id"] = int(category.id)
                items = list(user.allowed_items
                                 .select(Item.name, Item.description, Item.id)
                                 .where(Item.category == int(filter_category))
                                 .dicts())
                logger.debug("Got items filtered by category and user")
            else:
                payload["category_name"] = "All"
                items = list(user.allowed_items
                             .select(Item.name, Item.description, Item.id)
                             .dicts())
                logger.debug("Got all items")
            for item in items:
                services = list(user.allowed_services
                                    .select(Service.id, Service.name)
                                    .where(Service.item == item["id"])
                                    .dicts())
                item["services"] = services
            payload["items"] = items
            res.status = falcon.HTTP_200
            res.body = json.dumps(payload)
            logger.debug("Items request succesful")
        except Exception as e:
            print(e)
            logger.error(e)
            error_msg = ("Unable to get the items. Please try again later")
            raise falcon.HTTPServiceUnavailable(title=req.method + " failed",
                                                description=error_msg,
                                                retry_after=30,
                                                href=settings.__docs__)

    @falcon.before(login_required)
    def on_post(self, req, res):

        """Save a new item
        """
        try:
            # Parse token and get user id
            user_id = parse_token(req)['sub']
            # Get the user
            user = User.get(User.id == int(user_id))
            logger.debug("Got user data")
        except Exception as e:
            logger.error("Can't verify user")
            raise falcon.HTTPBadRequest(title="Bad request",
                                        description=e,
                                        href=settings.__docs__)

        try:
            raw_json = req.stream.read()
            logger.debug("Got incoming JSON data")
        except Exception as e:
            logger.error("Can't read incoming data stream")
            raise falcon.HTTPBadRequest(title="Bad request",
                                        description=e,
                                        href=settings.__docs__)

        try:
            result_json = json.loads(raw_json.decode("utf-8"), encoding='utf-8')
            logger.debug("Parsed JSON data")
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_400,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect.')

        try:
            new_item = Item.create(name=result_json.get('name'),
                                   description=result_json.get("description", ''),
                                   category=result_json.get("category"),
                                   tags=result_json.get("tags", ''))
            new_item.save()
            new_item.allowed_users.add(user)
            logger.debug("Saved new item into the database")
        except Exception as e:
            raise falcon.HTTPInternalServerError(title="Error while saving the item",
                                                 description=e,
                                                 href=settings.__docs__)

    def on_options(self, req, res):

        """Acknowledge the OPTIONS method.
        """
        res.status = falcon.HTTP_200

    def on_put(self, req, res):
        raise falcon.HTTPError(falcon.HTTP_405,
                               title="Client error",
                               description=req.method + " method not allowed.",
                               href=settings.__docs__)

    def on_update(self, req, res):
        raise falcon.HTTPError(falcon.HTTP_405,
                               title="Client error",
                               description=req.method + " method not allowed.",
                               href=settings.__docs__)

    def on_delete(self, req, res):
        raise falcon.HTTPError(falcon.HTTP_405,
                               title="Client error",
                               description=req.method + " method not allowed.",
                               href=settings.__docs__)


class DetailItem(object):

    """Show details of a specific category or add/delete a category
    """
    @falcon.before(login_required)
    def on_get(self, req, res, id):
        user_id = parse_token(req)['sub']
        try:
            user = User.get(User.id == int(user_id))
            item = Item.get(Item.id == int(id))
            if user not in item.allowed_users:
                raise falcon.HTTPForbidden(title="Permission denied",
                                           description="You don't have access to this resource",
                                           href=settings.__docs__)
            res.status = falcon.HTTP_200
            res.body = json.dumps(item)
            logger.debug("Items request succesful")
        except Exception as e:
            print(e)
            error_msg = ("Unable to get the item. Please try again later.")
            raise falcon.HTTPServiceUnavailable(req.method + " failed",
                                                description=error_msg,
                                                retry_after=30,
                                                href=settings.__docs__)

    @falcon.before(login_required)
    def on_put(self, req, res, id):
        try:
            # Parse token and get user id
            user_id = parse_token(req)['sub']
            # Get the user
            user = User.get(User.id == int(user_id))
        except Exception as e:
            logger.error("Can't verify user")
            raise falcon.HTTPBadRequest(title="Bad request",
                                        description=e,
                                        href=settings.__docs__)
        try:
            raw_json = req.stream.read()
            logger.debug("Got incoming JSON data")
        except Exception as e:
            logger.error("Can't read incoming data stream")
            raise falcon.HTTPBadRequest(title="Bad request",
                                        description=e,
                                        href=settings.__docs__)
        try:
            result_json = json.loads(raw_json.decode("utf-8"), encoding='utf-8')
        except ValueError:
            raise falcon.HTTPError(falcon.HTTP_400,
                                   'Malformed JSON',
                                   'Could not decode the request body. The '
                                   'JSON was incorrect.')
        try:
            item = Item.get(Item.id == int(id))
            if user not in item.allowed_users:
                raise falcon.HTTPForbidden(title="Permission denied",
                                           description="You don't have access to this resource",
                                           href=settings.__docs__)
            item.name = result_json.get("name", item.name)
            item.description = result_json.get("description", item.description)
            item.category = result_json.get("category", item.category)
            item.tags = result_json.get("tags", item.tags)
            item.save()
            res.status = falcon.HTTP_200
            res.body = json.dumps({"message": "Item updated"})
        except Exception as e:
            print(e)
            error_msg = ("Unable to get the item. Please try again later.")
            raise falcon.HTTPServiceUnavailable(req.method + " failed",
                                                description=error_msg,
                                                retry_after=30,
                                                href=settings.__docs__)

    @falcon.before(login_required)
    def on_delete(self, req, res, id):
        try:
            # Parse token and get user id
            user_id = parse_token(req)['sub']
            # Get the user
            user = User.get(User.id == int(user_id))
        except Exception as e:
            logger.error("Can't verify user")
            raise falcon.HTTPBadRequest(title="Bad request",
                                        description=e,
                                        href=settings.__docs__)
        try:
            item = Item.get(Item.id == int(id))
            if user not in item.allowed_users:
                raise falcon.HTTPForbidden(title="Permission denied",
                                           description="You don't have access to this resource",
                                           href=settings.__docs__)
            item.delete_instance()
            res.status = falcon.HTTP_200
            res.body = json.dumps({"message": "Deletion successful"})

        except Exception as e:
            print(e)
            error_msg = ("Unable to delete category. Please try again later.")
            raise falcon.HTTPServiceUnavailable(title="{0} failed".format(req.method),
                                                description=error_msg,
                                                retry_after=30,
                                                href=settings.__docs__)

    def on_options(self, req, res, id):

        """Acknowledge the OPTIONS method.
        """
        res.status = falcon.HTTP_200

    def on_post(self, req, res, id):
        raise falcon.HTTPError(falcon.HTTP_405,
                               title="Client error",
                               description=req.method + " method not allowed.",
                               href=settings.__docs__)

    def on_update(self, req, res):
        raise falcon.HTTPError(falcon.HTTP_405,
                               title="Client error",
                               description=req.method + " method not allowed.",
                               href=settings.__docs__)
