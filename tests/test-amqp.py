
import logSetup
logSetup.initLogging()

import FeedScrape.AmqpInterface
import settings

def test():
	print(FeedScrape.AmqpInterface.AmqpConnector)
	amqp_settings = {}
	amqp_settings["RABBIT_CLIENT_NAME"] = settings.RABBIT_CLIENT_NAME
	amqp_settings["RABBIT_LOGIN"]       = settings.RABBIT_LOGIN
	amqp_settings["RABBIT_PASWD"]       = settings.RABBIT_PASWD
	amqp_settings["RABBIT_SRVER"]       = settings.RABBIT_SRVER
	amqp_settings["RABBIT_VHOST"]       = settings.RABBIT_VHOST

	rq = FeedScrape.AmqpInterface.RabbitQueueHandler(settings=amqp_settings)
	print(rq)


if __name__ == "__main__":

	test()

