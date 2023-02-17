FROM nvcr.io/nvidia/pytorch:22.10-py3

RUN apt update -y && apt install openssh-server fish tmux -y

RUN mkdir /var/run/sshd

WORKDIR /tmp

RUN echo 'root:password' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#UsePAM yes/UsePAM no/' /etc/ssh/sshd_config
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd
RUN curl -LO "https://dl.k8s.io/"(curl -L -s https://dl.k8s.io/release/stable.txt)"/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

WORKDIR /root

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
